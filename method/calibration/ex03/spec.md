# vat specification (synthetic)

| Id | Level | Requirement | Test |
| --- | --- | --- | --- |
| REQ-001 | MUST | `gross_cents(net_cents, rates, country)` returns the net amount plus value added tax (VAT) at the percentage that `rates.percent(country)` gives, in whole cents, with halves rounded up. | `test_gross_adds_vat_and_rounds` |
| REQ-002 | MUST | The rate is looked up for the country given. The default country is `DE`. | `test_rate_looked_up_for_country` |
