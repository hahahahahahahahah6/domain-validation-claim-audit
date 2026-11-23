import tempfile
import unittest
from pathlib import Path
from domain_validation_claim_audit.audit import audit, evidence, matches, prose
from domain_validation_claim_audit.phrases import DOMAINVALIDATION, NODOMAINVALIDATION, GENERIC_NAMES

class AuditTests(unittest.TestCase):
    def test_phrases(self):
        for phrase in DOMAINVALIDATION:
            with self.subTest(phrase=phrase): self.assertTrue(matches(phrase)[0])
        for phrase in NODOMAINVALIDATION:
            with self.subTest(phrase=phrase): self.assertEqual(matches(phrase), ([], [phrase]))
        self.assertEqual(matches("```\nvalidate domain\n```"), ([], []))

    def test_routes(self):
        cases = ['import validators as v; v.domain(x)', 'from validators import domain as d; d(x)', 'import fqdn as f; f.FQDN(x).is_valid', 'from fqdn import FQDN as F; x = F(y); x.is_valid_absolute', 'from fqdn import FQDN\nwith FQDN(x) as f: f.is_valid_relative', 'obj.validate_domain(x)', 'from other import validate_domain as v; v(x)']
        cases += ['obj.' + name + '(x)' for name in GENERIC_NAMES]
        for code in cases:
            with self.subTest(code=code): self.assertTrue(evidence(code))

    def test_not_evidence(self):
        cases = ['import validators', 'domain(x)', 'fqdn(x)', 'FQDN(x)', 'x.domain(y)', 'x.FQDN(y)', 'import fqdn; fqdn.FQDN(x)', 'x.absolute', 'x.relative', 'x.is_valid', 'import validators; validators.hostname(x)', 'import re; re.match(".*", x)', 'import re; re.search(".*", x)', 'import re; re.fullmatch(".*", x)', 'import tldextract; tldextract.extract(x)', 'import tldextract; tldextract.get_tld(x)', 'import publicsuffix2; publicsuffix2.get_sld(x)', 'import publicsuffix2; publicsuffix2.get_public_suffix(x)', 'import idna; idna.encode(x)', 'import idna; idna.decode(x)', 'import dns.resolver; dns.resolver.resolve(x)', 'import socket; socket.gethostbyname(x)', 'import socket; socket.getaddrinfo(x, 80)', 'import validators; validators.url(x)', 'import validators; validators.ipv4(x)', 'import validators; validators.ipv6(x)', 'import validators; validators.email(x)', 'import validators; validators.card_number(x)', 'from urllib.parse import urlparse; urlparse(x)', 'from urllib.parse import urlsplit; urlsplit(x)', 'import subprocess; subprocess.run(["validate_domain"])', '"validate domain"', '# validate domain', 'import validators; validators = object(); validators.domain(x)', 'from validators import domain; def domain(): pass', 'import fqdn; fqdn.FQDN(x).is_valid()','obj.validate_domain']
        for code in cases:
            with self.subTest(code=code): self.assertFalse(evidence(code))

    def test_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp); (p/'README.md').write_text('validate domain')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')
            (p/'tests').mkdir(); (p/'tests/test_x.py').write_text('import validators; validators.domain(x)')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'MEDIUM')
            (p/'app.py').write_text('import validators; validators.domain(x)')
            self.assertFalse(audit(p)['findings'])
            (p/'README.md').write_text('no domain validation')
            self.assertEqual(audit(p)['findings'][0]['severity'], 'HIGH')
            (p/'app.py').write_text('import fqdn; x = fqdn.FQDN(y)')
            (p/'other.py').write_text('x.is_valid')
            self.assertFalse(audit(p)['findings'])

    def test_self_audit(self):
        root=Path(__file__).resolve().parents[1]
        self.assertFalse(audit(root)['findings'])
        self.assertFalse(audit(root/'README.md')['findings'])

    def test_limitations(self):
        root=Path(__file__).resolve().parents[1]
        text=(root/'README.md').read_text().split('## Limitations', 1)[1]
        self.assertEqual(matches(text), ([], []))

if __name__ == '__main__': unittest.main()
