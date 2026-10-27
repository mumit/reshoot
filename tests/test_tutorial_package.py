"""Portable workshop downloads retain audited media and work outside the capture directory."""
import importlib.util
import hashlib
import json
from pathlib import Path
import zipfile

import pytest

spec=importlib.util.spec_from_file_location('tutorial_package',Path(__file__).resolve().parents[1]/'examples/tutorial/package.py')
package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)


def attempt(root):
    exports=root/'exports';exports.mkdir(parents=True)
    audit={'review_status':'pending','scan':{'status':'completed','flagged':0},'exports':{}}
    for name in ('tutorial','first-demo'):
        (exports/(name+'.mp4')).write_bytes(('Synthetic video '+name).encode())
        (exports/(name+'.srt')).write_text('1\n00:00:00,000 --> 00:00:02,000\nA synthetic lesson.\n')
        (exports/(name+'.vtt')).write_text('WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nA synthetic lesson.\n')
        (exports/(name+'-chapters.json')).write_text(json.dumps([{'start':0,'end':2,'title':'A synthetic lesson'}]))
        audit['exports'][name]={'sha256':package.sha(exports/(name+'.mp4')),'seconds':420 if name=='tutorial' else 150}
    (exports/'transcript.md').write_text('# Synthetic workshop\n\nA synthetic lesson.\n')
    (root/'audit.json').write_text(json.dumps(audit))
    return root


def test_bundle_preserves_audited_files_and_has_only_portable_paths(tmp_path):
    source=attempt(tmp_path/'attempt')
    destination=tmp_path/'delivery'
    archive=package.package(source,destination,'a'*40)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        names=bundle.namelist()
        assert all(name.startswith('reshoot-workshop/') and '..' not in name for name in names)
        manifest=json.loads(bundle.read('reshoot-workshop/manifest.json'))
        assert manifest['source_review_status']=='pending'
        for name,digest in manifest['files'].items():
            assert hashlib.sha256(bundle.read('reshoot-workshop/'+name)).hexdigest()==digest
        for name in ('tutorial','first-demo'):
            assert bundle.read('reshoot-workshop/'+name+'.mp4')==(source/'exports'/(name+'.mp4')).read_bytes()
        player=bundle.read('reshoot-workshop/watch.html').decode()
        assert str(source) not in player and '127.0.0.1' not in player
        assert 'data-seek="0.000"' in player and 'transcript.md' in player
    assert (destination/'SHA256SUMS').read_text().startswith(package.sha(archive))
    assert '00:00 A synthetic lesson' in (destination/'tutorial-upload.txt').read_text()
    notes=(destination/'release-notes.md').read_text()
    assert 'workshop-*' in notes and 'about 7 minutes' in notes and 'about 2.5 minutes' in notes


@pytest.mark.parametrize('change',['video','transcript'])
def test_stale_or_incomplete_attempt_is_rejected_before_packaging(tmp_path,change):
    source=attempt(tmp_path/'attempt')
    if change=='video':(source/'exports/tutorial.mp4').write_bytes(b'Changed synthetic video')
    else:(source/'exports/transcript.md').unlink()
    with pytest.raises(ValueError):package.package(source,tmp_path/'delivery','a'*40)
    assert not (tmp_path/'delivery').exists()
