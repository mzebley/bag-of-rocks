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
        (tester/'trace.json').write_text(json.dumps({'header':{'run_id':'fixture'},'steps':[step],'end':{'belief':'Done','stop_reason':'apparent completion'}}))
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

if __name__=='__main__':
    unittest.main()
