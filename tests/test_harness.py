"""Offline regression checks; never launches a browser or modifies installed skills."""
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9X8AAAAASUVORK5CYII=')

class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)

    def call(self, script, *args):
        return subprocess.run([sys.executable, str(ROOT/'scripts'/script), *map(str,args)], capture_output=True, text=True)

    def packet(self, **changes):
        params = json.loads((ROOT/'examples/run-params.json').read_text())
        params['output_dir'] = str(self.run/'tester')
        params.update(changes)
        path = self.run/'run-params.json'
        path.write_text(json.dumps(params))
        return self.call('build_packet.py',path,'--strict')

    def trace(self, **changes):
        tester=self.run/'tester';tester.mkdir(exist_ok=True)
        (tester/'before.jpg').write_bytes(PNG) # deliberate extension mismatch
        (tester/'after.png').write_bytes(PNG)
        step={'id':'C1','screenshot':'before.jpg','result_screenshot':'after.png','cue':'Save button','expectation':'Saved','action':'Click','result':'Saved banner','traits':['ordinary'],'clicks':[{'px':[0.5,0.25],'approx':True}],'ignored':[{'box_px':[0,0,1,1],'label':'Hint'}]}
        step.update(changes)
        (tester/'trace.json').write_text(json.dumps({'header':{'run_id':'fixture'},'steps':[step],'end':{'belief':'Done','stop_reason':'believed complete'}}))
        return tester

    def test_packet_is_deterministic_and_hash_matches(self):
        self.assertEqual(self.packet().returncode,0)
        p=(self.run/'tester-packet.txt').read_bytes()
        digest=(self.run/'tester-packet.sha256').read_text().split()[0]
        self.assertEqual(digest,hashlib.sha256(p).hexdigest())
        self.assertEqual(self.packet().returncode,0)
        self.assertEqual(p,(self.run/'tester-packet.txt').read_bytes())

    def test_hidden_context_is_not_in_packet_and_strict_warns(self):
        result=self.packet(intended_path='PRIVATE_ROUTE_SENTINEL',inherited_state='PRIVATE_STATE_SENTINEL')
        self.assertNotEqual(result.returncode,0)
        packet=(self.run/'tester-packet.txt').read_text()
        self.assertNotIn('PRIVATE_ROUTE_SENTINEL',packet)
        self.assertNotIn('PRIVATE_STATE_SENTINEL',packet)
        self.assertIn('intended_path',result.stdout)

    def test_trait_selection_changes_packet_and_fixed_input_survives(self):
        self.assertEqual(self.packet(preset='patient-bag',traits_add=['Autofill Truster'],phrasing={'fixed':'Where is my address?'}).returncode,0)
        packet=(self.run/'tester-packet.txt').read_text()
        self.assertIn('active traits: VPF, HTS, FC, LIT, NR, AT',packet)
        self.assertIn('Where is my address?',packet)
        self.assertIn('Low Patience is off',packet)

    def test_unknown_trait_fails_before_packet_creation(self):
        self.assertNotEqual(self.packet(traits_add=['NOT_A_TRAIT']).returncode,0)
        self.assertFalse((self.run/'tester-packet.txt').exists())

    def test_conversion_uses_image_bytes_and_preserves_frozen_files(self):
        tester=self.trace()
        before={f.name:f.read_bytes() for f in tester.iterdir()}
        result=self.call('trace_to_run.py',self.run)
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads((self.run/'run.json').read_text())
        c=data['steps'][0]['clicks'][0]
        self.assertEqual((c['x'],c['y'],c['approx']),(50,25,True))
        self.assertEqual(data['steps'][0]['ignored'][0]['w'],100)
        self.assertTrue(any('extensions' in x for x in data['limits']))
        self.assertEqual(before,{f.name:f.read_bytes() for f in tester.iterdir()})

    def test_pending_missing_result_and_missing_image_are_reported(self):
        self.trace(result='pending',result_screenshot='',screenshot='missing.png',clicks=[{'x':20,'y':30}])
        result=self.call('trace_to_run.py',self.run)
        self.assertEqual(result.returncode,0,result.stderr)
        limits=' '.join(json.loads((self.run/'run.json').read_text())['limits'])
        for problem in ['pending','no result_screenshot','Screenshot missing']:
            self.assertIn(problem,limits)

    def test_existing_review_is_not_overwritten(self):
        self.trace()
        (self.run/'run.json').write_text('{"reviewer":"keep"}')
        self.assertEqual(self.call('trace_to_run.py',self.run).returncode,0)
        self.assertEqual((self.run/'run.json').read_text(),'{"reviewer":"keep"}')

    def test_calibration_is_explicit_and_does_not_change_run_data(self):
        self.assertNotEqual(self.call('trace_to_run.py', self.run, '--calibration').returncode, 0)
        self.trace()
        self.assertEqual(self.call('trace_to_run.py', self.run).returncode, 0)
        original = (self.run/'run.json').read_bytes()
        for flags, enabled in [(('--calibration',), 'true'), ((), 'false')]:
            result = self.call('trace_to_run.py', self.run, '--filmstrip', *flags)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f'const CALIBRATION = {enabled};', (self.run/'filmstrip.html').read_text())
            self.assertEqual(original, (self.run/'run.json').read_bytes())

    def test_filmstrip_embeds_json_without_closing_script(self):
        self.trace()
        self.assertEqual(self.call('trace_to_run.py',self.run).returncode,0)
        data=json.loads((self.run/'run.json').read_text())
        data['run']['goal']='</script><script>throw new Error("fixture")</script>'
        (self.run/'run.json').write_text(json.dumps(data))
        result=self.call('trace_to_run.py',self.run,'--filmstrip')
        self.assertEqual(result.returncode,0,result.stderr)
        html=(self.run/'filmstrip.html').read_text()
        embedded=re.search(r'<script id="run-data" type="application/json">(.*?)</script>',html,re.S).group(1)
        self.assertEqual(json.loads(embedded),data)
        self.assertNotIn(data['run']['goal'],html)

    def test_lint_covers_every_tester_visible_field(self):
        for changes in [{'run_id':'retest-after-fix'},{'phrasing':{'fixed':'click the "Edit" link'}},
                        {'prohibited_effects':['Avoid the known bug']},{'goal':'Change my address. Hint: it is under Account.'}]:
            self.assertNotEqual(self.packet(**changes).returncode,0,changes)

    def test_answer_key_labels_are_flagged(self):
        (self.run/'coordinator').mkdir()
        (self.run/'coordinator/intended-path.json').write_text(json.dumps({'steps':[{'id':'I1','intended_cue':'"Edit" link beside address'}]}))
        result=self.packet(goal='Edit my mailing address')
        self.assertNotEqual(result.returncode,0)
        self.assertIn("answer-key label 'Edit'",result.stdout)

    def test_production_host_forces_no_mutations_unless_declared(self):
        self.assertEqual(self.packet(start_url='https://www.example.com/',mutations='allowed').returncode,0)
        self.assertEqual(json.loads((self.run/'tester-packet.json').read_text())['mutations'],'none')
        (self.run/'.bag-of-rocks').mkdir()
        (self.run/'.bag-of-rocks/config.json').write_text(json.dumps({'environments':{'qa':{'base_url':'https://www.example.com','mutations':'allowed','prohibited':['Emails']}}}))
        self.assertEqual(self.packet(start_url='https://www.example.com/',mutations='allowed').returncode,0)
        packet=(self.run/'tester-packet.txt').read_text()
        self.assertIn('Mutations: allowed',packet)
        self.assertIn('Emails',packet)

    def test_preset_intensity_and_config_default_preset(self):
        (self.run/'.bag-of-rocks').mkdir()
        (self.run/'.bag-of-rocks/config.json').write_text(json.dumps({'default_preset':'rushed','presets':{'rushed':['VPF','FC:5']}}))
        self.assertEqual(self.packet(preset=None).returncode,0)
        packet=(self.run/'tester-packet.txt').read_text()
        self.assertIn('active traits: VPF, FC',packet)
        self.assertIn('up to 5 extra clicks',packet)

    def test_conversion_checks_header_traits_and_stop_reason(self):
        self.packet()
        self.trace(traits=['TW','ordinary'])
        trace=json.loads((self.run/'tester/trace.json').read_text())
        trace['header'].update(goal='Something else',traits=['VPF'])
        trace['end']['stop_reason']='gave up'
        (self.run/'tester/trace.json').write_text(json.dumps(trace))
        self.call('trace_to_run.py',self.run)
        data=json.loads((self.run/'run.json').read_text())
        limits=' '.join(data['limits'])
        for problem in ['Header goal','Header traits','mixes','TW',"Unknown stop_reason"]:
            self.assertIn(problem,limits)
        self.assertEqual(data['run']['packet_sha256'],(self.run/'tester-packet.sha256').read_text().split()[0])
        self.assertEqual(data['run']['phrasing'],'own-words')

    def test_yaml_style_intended_path_keys_and_assumptions(self):
        self.trace()
        (self.run/'coordinator').mkdir()
        (self.run/'coordinator/intended-path.json').write_text(json.dumps({'steps':[{'id':'I1','screen':'Account','intended_cue':'Edit','intended_action':'open'}],'assumptions':['User notices Edit']}))
        self.call('trace_to_run.py',self.run)
        data=json.loads((self.run/'run.json').read_text())
        self.assertEqual(data['intended'][0]['cue'],'Edit')
        self.assertEqual(data['assumptions'],[{'text':'User notices Edit','status':''}])

    def test_freeze_manifest_detects_tester_changes(self):
        tester=self.trace()
        self.call('trace_to_run.py',self.run)
        self.assertTrue((self.run/'tester.sha256').exists())
        (tester/'after.png').write_bytes(PNG+b'x')
        out=self.call('trace_to_run.py',self.run).stdout
        self.assertIn('changed after freezing: tester/after.png',out)

    def test_force_keeps_reviewer_fields(self):
        self.trace()
        self.call('trace_to_run.py',self.run)
        data=json.loads((self.run/'run.json').read_text())
        data['findings']=[{'id':'F1'}]; data['outcome']['supported']='uncertain'
        data['steps'][0]['divergence']={'from':'I1','kind':'recovered'}; data['limits'].append('Reviewer limit')
        (self.run/'run.json').write_text(json.dumps(data))
        self.assertEqual(self.call('trace_to_run.py',self.run,'--force').returncode,0)
        data=json.loads((self.run/'run.json').read_text())
        self.assertEqual(data['findings'],[{'id':'F1'}])
        self.assertEqual(data['outcome']['supported'],'uncertain')
        self.assertEqual(data['steps'][0]['divergence']['kind'],'recovered')
        self.assertEqual(data['limits'].count('Reviewer limit'),1)

    def test_viewport_click_space_scales_high_density_screenshots(self):
        tester=self.trace(clicks=[{'px':[1,1]}])
        trace=json.loads((tester/'trace.json').read_text())
        trace['header'].update(viewport={'width':2,'height':2})
        (tester/'trace.json').write_text(json.dumps(trace))
        self.call('trace_to_run.py',self.run)
        self.assertIn('click_space',' '.join(json.loads((self.run/'run.json').read_text())['limits']))
        trace['header']['click_space']='viewport'
        (tester/'trace.json').write_text(json.dumps(trace))
        (self.run/'tester.sha256').unlink()
        self.call('trace_to_run.py',self.run,'--force')
        c=json.loads((self.run/'run.json').read_text())['steps'][0]['clicks'][0]
        self.assertEqual((c['x'],c['y']),(50,50))

if __name__=='__main__':
    unittest.main()
