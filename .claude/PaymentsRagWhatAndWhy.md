# What Are We Building, and Why? (Plain-Language Version)

The problem, the jargon, and the use case for the payments RAG + agent project —
stripped of complexity.

---

## The two terms, in plain language

### SEPA — the rulebook for sending euros between banks in Europe
Think of it as the "rules of the road" for euro transfers. When someone in
Germany pays someone in France, SEPA is the agreed set of rules that makes that
work like a normal domestic transfer. It's a set of documents that say *how* it
must be done.

### ISO 20022 — the standard *format* banks use to write payment messages
Think of it as a very strict form with named boxes. Instead of every bank
inventing its own way to say "pay EUR 500 from account A to account B," they all
fill in the same form, with the same boxes in the same places, so computers on
both ends can read it automatically.

- **`pacs.008`** — the form banks use to actually move money between each other.
- **`pain.001`** — the form a company uses to tell its bank "please make these payments."

**In short:** SEPA = the rules. ISO 20022 = the standardized forms.

---

## The actual problem the tool solves

These rules and forms are documented in **hundreds of pages of dense, dry PDFs**.
Every payments engineer, at some point, needs to look something up in them — and
it's genuinely painful. It's `Ctrl-F` through a 200-page technical spec, hoping
you guess the right keyword.

Real questions an engineer actually has:

- *"I need to send the customer's invoice number with the payment so the
  receiver can match it. Which box in the pacs.008 form does that go in?"*
- *"What's the maximum length of the 'reference' field?"*
- *"Is this field required or optional for a SEPA instant payment?"*

Today, finding the answer means digging through the PDF. **The tool lets them ask
in plain English and get the answer — with a citation to the exact page** — so
they can trust it and verify.

---

## The use case, concretely

Someone opens the tool and types:

> "Where does the remittance information go in a pacs.008 message, and how long
> can it be?"

The tool:

1. Searches the payment-spec documents,
2. Finds the relevant paragraph,
3. Has Claude answer in plain English,
4. Shows *"Source: SEPA Credit Transfer Rulebook, p.47"* so it's trustworthy.

And because the fx tools are bolted on, it can also handle:

> "Is IBAN DE89370400440532013000 valid, and what's 5000 EUR in USD today?"

So it's a **payments knowledge assistant** — part "search the manuals for me,"
part "do the payments math for me."

---

## Why this is a smart choice for the relocation goal

The European fintech companies on the target list — Mollie, Adyen, ING, Bunq —
**live and breathe SEPA and ISO 20022 every single day.** It's their core
business. A portfolio project built on exactly the standards they work with says
*"I already understand your domain"* before the interview even starts. That's the
whole reason this corpus beats a generic one.

**Note:** Day-to-day work in the UAE is regional payment gateways (Aani, Pine
Labs), so SEPA isn't in daily use — which is why learning it now is a smart move,
not a gap. If a standard closer to current work or a global one is preferred,
**ISO 20022 on its own** also works well (it's the worldwide standard that
cross-border payments are migrating to). But SEPA + ISO 20022 aims straight at
the relocation targets.