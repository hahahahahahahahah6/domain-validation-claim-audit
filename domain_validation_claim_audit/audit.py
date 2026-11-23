"""Inspect documentation and static Python call shapes without executing code."""
import ast
import os
import re
from pathlib import Path
from .phrases import DOMAINVALIDATION, NODOMAINVALIDATION, GENERIC_NAMES



def normalize(text):
    return ' '.join(text.lower().replace("n't", ' not').replace('-', ' ').split())

def prose(text):
    output = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence) and not marker.group(2).strip():
                fence = None
            continue
        if marker:
            fence = marker.group(1)
            output.append('')
        else:
            output.append(line)
    return '\n'.join(output)

def matches(text):
    yes, no = [], []
    for paragraph in re.split(r'\n\s*\n', prose(text)):
        value = normalize(paragraph)
        for phrases, found in ((NODOMAINVALIDATION, no), (DOMAINVALIDATION, yes)):
            for phrase in sorted(phrases, key=lambda s: (-len(s), s)):
                pattern = r'(?<!\w)' + re.escape(phrase) + r'(?!\w)'
                if re.search(pattern, value):
                    found.append(phrase)
                    value = re.sub(pattern, ' ', value)
    return yes, no

def evidence(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    imports, defined, assigned = {}, set(), set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        if isinstance(node, ast.Import):
            for item in node.names:
                imports[item.asname or item.name.split('.')[0]] = item.name if item.asname else item.name.split('.')[0]
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for item in node.names:
                imports[item.asname or item.name] = node.module + '.' + item.name
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [item.optional_vars for item in node.items if item.optional_vars]
        for target in targets:
            assigned.update(n.id for n in ast.walk(target) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store))
    shadowed = defined | (assigned & imports.keys())

    def route(fn, library, names):
        if isinstance(fn, ast.Name):
            origin = imports.get(fn.id, '')
            return fn.id not in shadowed and origin in {library + '.' + n for n in names} and origin.rsplit('.', 1)[-1] not in defined
        if isinstance(fn, ast.Attribute) and fn.attr in names and fn.attr not in defined:
            base = fn.value
            while isinstance(base, ast.Attribute):
                base = base.value
            return isinstance(base, ast.Name) and base.id not in shadowed and imports.get(base.id) == library
        return False

    def construction(node):
        return isinstance(node, ast.Call) and route(node.func, 'fqdn', {'FQDN'})

    bound = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and construction(node.value):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            bound.update(t.id for t in targets if isinstance(t, ast.Name))
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if construction(item.context_expr) and item.optional_vars is not None:
                    bound.update(t.id for t in ast.walk(item.optional_vars)
                                 if isinstance(t, ast.Name) and isinstance(t.ctx, ast.Store))
    called_attributes = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in {'is_valid', 'is_valid_absolute', 'is_valid_relative'} and isinstance(node.ctx, ast.Load) and id(node) not in called_attributes:
            if construction(node.value) or (isinstance(node.value, ast.Name) and node.value.id in bound):
                return True
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if route(fn, 'validators', {'domain'}):
            return True
        if isinstance(fn, ast.Name):
            origin = imports.get(fn.id, '')
            if fn.id not in shadowed and origin and origin.rsplit('.', 1)[-1] in GENERIC_NAMES and origin.rsplit('.', 1)[-1] not in defined:
                return True
        elif isinstance(fn, ast.Attribute) and fn.attr in GENERIC_NAMES and fn.attr not in defined:
            base = fn.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if not isinstance(base, ast.Name) or base.id not in shadowed:
                return True
    return False

def audit(root, ignores=()):
    root = Path(root)
    if root.is_file() and not root.is_symlink():
        yes, no = matches(root.read_text(encoding='utf-8'))
        claims = [{'path': root.name, 'phrase': x} for x in yes]
        denials = [{'path': root.name, 'phrase': x} for x in no]
        findings = ([{'id': 'documented-domain-validation-claim-false', 'severity': 'HIGH', 'claims': claims}] if claims else [])
        return {'findings': findings, 'claims': claims, 'denials': denials, 'production_evidence': [], 'test_evidence': []}
    if root.is_symlink() or not root.is_dir() or not os.access(root, os.R_OK | os.X_OK):
        raise OSError('root is not a readable directory')
    prefixes = [s.replace('\\', '/').strip('/') for s in ignores]
    claims, denials, production, tests = [], [], [], []
    def ignored(path):
        rel = path.relative_to(root).as_posix()
        return any(rel == x or rel.startswith(x + '/') for x in prefixes if x)
    def onerror(error):
        raise error
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        parent = Path(directory)
        dirs[:] = sorted(d for d in dirs if not (parent / d).is_symlink() and not ignored(parent / d))
        for name in sorted(files):
            path = parent / name
            if path.is_symlink() or ignored(path):
                continue
            rel = path.relative_to(root)
            if rel == Path('README.md') or ('docs' in rel.parts and path.suffix == '.md'):
                yes, no = matches(path.read_text(encoding='utf-8'))
                claims.extend({'path': str(rel), 'phrase': x} for x in yes)
                denials.extend({'path': str(rel), 'phrase': x} for x in no)
            if path.suffix == '.py' and not set(rel.parts) & {'fixtures', 'docs', 'examples'}:
                if evidence(path.read_text(encoding='utf-8')):
                    is_test = 'tests' in rel.parts or name.startswith('test_') or name.endswith('_test.py')
                    (tests if is_test else production).append(str(rel))
    findings = []
    if claims and not production:
        findings.append({'id': 'documented-domain-validation-claim-false', 'severity': 'MEDIUM' if tests else 'HIGH', 'claims': claims})
    if denials and production:
        findings.append({'id': 'documented-no-domain-validation-claim-false', 'severity': 'HIGH', 'claims': denials})
    return {'findings': findings, 'claims': claims, 'denials': denials, 'production_evidence': production, 'test_evidence': tests}
