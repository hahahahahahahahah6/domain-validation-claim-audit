# Claim audit

This offline tool compares documentation with static Python source. It reads the root README and Markdown under a docs directory; fenced blocks are ignored and inline code is included. It never executes inspected code.

Install and run:

```sh
python3 -m pip install .
python3 -m domain_validation_claim_audit audit . --json
domain-validation-claim-audit audit . --verbose
```

Use `--ignore` repeatedly for path prefixes and `--fail-on medium` to include test-only evidence in the failure threshold. Exit codes are 0 for pass, 2 for findings at the threshold, and 1 for usage or input errors.

Findings:

```
documented-domain-validation-claim-false
documented-no-domain-validation-claim-false
```

## Differentiation

This tool concerns the shape of a bare host name. It does not cover generic input checks, JSON field names, account ownership, authentication, password verification, password hashing, password generation, PDF encryption, email or SMS sending, document extraction, barcode scanning, email or phone number checks, password strength, JSON Schema, dates, taking a payment from a card, reading card details out of a document, checking whether a card number passes its checksum, JSON decoding, regex matching, URL parsing or fetching, DNS resolution, URL checks, IP address checks, or ISBN checks. Other families cover spreadsheet, word document and presentation reading and generation; PDF extraction, generation, merging, splitting, rotation, forms, watermarking, redaction, compression and annotation; tables, OCR, signatures, screen recording, video, QR codes, barcode generation, audio mixing, generation and editing, source separation, speech recognition, text to speech, noise suppression, music generation and transcription.

## Limitations

This phrase can refer to a remote policy check, producing a false positive; a human must decide.

```
validate domain
```

This phrase can refer to a manual runbook step, producing a false positive; a human must decide.

```
check domain
```

This phrase can refer to a roadmap item, producing a false positive; a human must decide.

```
domain validation
```

This phrase can refer to a hosted page, producing a false positive; a human must decide.

```
domain validator
```

This phrase can refer to reader advice, producing a false positive; a human must decide.

```
valid domain
```

This phrase can refer to a successful lookup, producing a false positive; a human must decide.

```
domain is valid
```

This phrase can refer to a specification section, producing a false positive; a human must decide.

```
domain name validation
```

This phrase can refer to a design discussion, producing a false positive; a human must decide.

```
fqdn validation
```

This phrase can refer to an allow-list check, producing a false positive; a human must decide.

```
validate hostname
```

This phrase can refer to a remote service check, producing a false positive; a human must decide.

```
hostname validation
```

This phrase can refer to reader advice, producing a false positive; a human must decide.

```
valid hostname
```

This phrase can refer to ownership verification, producing a false positive; a human must decide.

```
verify domain
```

This phrase can refer to a length-only rule, producing a false positive; a human must decide.

```
detect invalid domain
```

This phrase can refer to a theoretical discussion, producing a false positive; a human must decide.

```
domain well formed
```

This phrase can refer to a generated value, producing a false positive; a human must decide.

```
is valid domain
```

The FQDN pair is a static shape and can appear in code that never runs.

A hostname call is excluded because it also accepts other shapes.

A DNS lookup is excluded because existence does not establish syntax.

A suffix extraction call is excluded because it only splits a name.

A public suffix lookup is excluded because it only looks up a suffix.

An IDNA encoding call is excluded because it transforms a name.

Module aliases passed through variable chains can be missed.

Bare imports do not count.

Roadmap prose is still treated as a claim.

Changelog prose is still treated as a claim.

TODO prose is still treated as a claim.

Denials outside the fixed list may be missed.

Other documentation locations are not read.

Evidence split across modules is missed.

Local definitions shadow route names.

Dead code counts.

Subprocess calls do not count.

A generic input check does not establish the relevant capability.

An email check alone does not count.

A telephone number check alone does not count.

A web address check alone does not count.

A numeric address check alone does not count.

An extraction call alone does not count.

A locally defined generic name is shadowed.

Generic aliases passed through chains can be missed.

Only exact phrases are matched, not meaning.

Only Python source is inspected.

Runtime imports and plugins are invisible.

A construction alone does not count.

Formatting attributes alone do not count.

A regular expression match alone does not count.
