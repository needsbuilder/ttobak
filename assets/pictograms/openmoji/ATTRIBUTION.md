# OpenMoji — attribution

Source: https://openmoji.org · repo: https://github.com/hfg-gmuend/openmoji
(color/svg set) · **release pin: 17.0.0 (published 2026-04-23), files verified
against upstream 2026-07-06.** OpenMoji periodically redesigns individual glyphs
and `master` is a moving target, so the release tag is pinned here for provenance.

"All emojis designed by OpenMoji – the open-source emoji and icon project.
License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)"

## Files (unmodified, renamed from hexcode to concept name)

| File | OpenMoji annotation | hexcode |
|---|---|---|
| money.svg | money bag | 1F4B0 |
| pay.svg | credit card | 1F4B3 |
| tax.svg | receipt | 1F9FE |
| calendar.svg | calendar | 1F4C5 |
| deadline.svg | alarm clock | 23F0 |
| apply.svg | memo | 1F4DD |
| address.svg | round pushpin | 1F4CD |
| health.svg | stethoscope | 1FA7A |
| insurance.svg | shield | 1F6E1 |
| bank_account.svg | ledger (통장) | 1F4D2 |
| mail.svg | envelope | 2709 |
| email.svg | e-mail | 1F4E7 |
| website.svg | globe with meridians | 1F310 |
| support.svg | handshake | 1F91D |
| benefit.svg | wrapped gift | 1F381 |
| warning.svg | warning | 26A0 |
| forbidden.svg | no entry | 26D4 |
| place.svg | world map | 1F5FA |

## Why some of these moved from "mulberry" to "openmoji"

`lexicon.py` originally assigned money/pay/tax/calendar/deadline/apply/address/health/
insurance/bank_account/mail/support/benefit/place to the Mulberry set. Mulberry Symbols
is an AAC (communication board) vocabulary — concrete, everyday concepts — and its
`symbol-info.csv` (3436 symbols) has no usable entry for these more abstract
administrative/legal concepts (tax, insurance, deadline, application, benefit, bank
account, address, mail as a noun). OpenMoji was already the project's documented
"secondary" pictogram set for exactly this kind of gap (spec §9.4), so these concepts
were re-pointed there instead of forcing a poor-fit Mulberry symbol. `health` also moved
here so it reads visually distinct from `hospital` (both would otherwise reuse Mulberry's
single clinic-building symbol).

`money` (돈/금액) and `bank_account` (계좌) were fixed after an adversarial review
(2026-07-06): they previously collapsed onto Mulberry's bank-building glyph
(`money.svg` was a byte-identical copy of `bank.svg`, and `bank_account.svg` was
OpenMoji's bank-building emoji 1F3E6), so 돈·계좌·은행 all rendered as the same
building. `money` now uses OpenMoji money bag (1F4B0) and `bank_account` uses
OpenMoji ledger/passbook (1F4D2), leaving `은행` on the Mulberry bank building —
three visually distinct glyphs. See the financial-cluster note in `lexicon.py`.

No pixels/paths modified — files are renamed copies only (spec §9.4 "unmodified" tier).
