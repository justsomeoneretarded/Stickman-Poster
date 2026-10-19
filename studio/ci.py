"""Restore authenticated encrypted private voice profiles on an Actions runner."""
import hashlib
import hmac
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path


def restore_profiles(archive, signature, destination, key):
    archive, destination = Path(archive), Path(destination)
    signing_key = hashlib.sha256(b'stickman-profile-auth-v1:' + key.encode()).digest()
    actual = hmac.new(signing_key, archive.read_bytes(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(actual, Path(signature).read_text().strip()):
        raise ValueError('Voice archive authentication failed; check VOICE_PROFILE_KEY')
    destination.mkdir(parents=True, exist_ok=True)
    # OpenSSL reads the password from a private file, never a process argument/log.
    with tempfile.TemporaryDirectory() as scratch:
        password, clear = Path(scratch)/'key', Path(scratch)/'profiles.tar.gz'
        password.write_text(key+'\n'); password.chmod(0o600)
        subprocess.run(['openssl', 'enc', '-d', '-aes-256-cbc', '-pbkdf2', '-iter', '200000',
                        '-in', str(archive), '-out', str(clear), '-pass', 'file:'+str(password)], check=True)
        with tarfile.open(clear, 'r:gz') as tar:
            allowed = {'cast-profiles.json'}
            for speaker in ('female', 'male1-kit-laser', 'male2-warguy'):
                allowed |= {f'profiles/{speaker}/profile.json', f'profiles/{speaker}/conditioning.pt'}
            if {m.name for m in tar.getmembers()} != allowed or any(not m.isfile() for m in tar.getmembers()):
                raise ValueError('Unexpected voice archive contents')
            tar.extractall(destination, filter='data')
    print('Private profiles restored; no source recordings included', flush=True)


if __name__ == '__main__':
    key = os.environ.get('VOICE_PROFILE_KEY', '').strip()
    if not key:
        raise SystemExit('Missing repository Actions secret VOICE_PROFILE_KEY. See docs/ACTIONS.md; no stock voice fallback will be used.')
    restore_profiles('ci/voice-profiles.tar.gz.enc', 'ci/voice-profiles.hmac', 'private', key)
