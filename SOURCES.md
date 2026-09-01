# Sources

Every historical value in this simulation is one of three things: verified
against a document in this repository, sourced externally and marked as such,
or explicitly recorded as the simulation's own invention. This file is the
map for the first two.

## What ships in the repository

The `attached_assets/` directory holds the searchable text of the documents
the code cites. They are plain text, so a claim in a docstring can be checked
with `grep`:

```
grep -n "1300 ohms" attached_assets/Engineering_and_Operations_in_the_Bell_System_2ed_1984_djvu.txt
```

### Most cited

| Document | Cited for |
| --- | --- |
| Engineering and Operations in the Bell System, 2nd ed. (1984) | Switching hierarchy and machine capacities, the corrective maintenance sequence, loop design limits (1300 and 1500 ohms with their length bands), coin station line current, the N0/1X area code format, NSPMP measurement weights |
| Telecommunications Transmission Engineering, Vols. 1-3 (1977) | L-carrier spectra, 1004 Hz loss objectives, local cable capacitance at 0.083 uF/mile, balance test lines, SF signalling levels |
| Bell System Technical Journal (1976-1982) | The 100/102/105-type far-end test line series, the remote office test line and 52A responder, CAROT, the processor controlled interrogator, channel maintenance states |

### Full text inventory

Sixty-five files, 968,959 lines and 2,668,827 words of searchable
text. Counted in lines and words rather than megabytes because that is
what the number is for: these are grepped, and `grep -n` answers in
line numbers.

| File | Lines | Words |
| --- | ---: | ---: |
| `00 Frontmatter and Table of Contents_djvu.txt` | 127 | 215 |
| `01 Introduction_djvu.txt` | 64 | 303 |
| `01 UNIX Documentation Road Map_djvu.txt` | 657 | 2,526 |
| `02 Administrative Advice (DEC)_djvu.txt` | 1,065 | 5,425 |
| `02 Editor Tutorial_djvu.txt` | 1,668 | 6,377 |
| `03 Administrative Advice (3B20S)_djvu.txt` | 759 | 4,093 |
| `03 UNIX for Beginners_djvu.txt` | 2,086 | 8,892 |
| `04 Setting Up The UNIX System (DEC)_djvu.txt` | 1,861 | 10,880 |
| `04 UNIX Shell Tutorial_djvu.txt` | 3,006 | 17,959 |
| `05 C Reference Manual_djvu.txt` | 2,517 | 13,620 |
| `05 Setting Up The UNIX System (3B20)_djvu.txt` | 2,254 | 12,219 |
| `06 Auto Call Facility Installation_djvu.txt` | 254 | 1,166 |
| `06 UNIX Programming_djvu.txt` | 1,722 | 9,928 |
| `07 UNIX System Accounting_djvu.txt` | 1,851 | 7,627 |
| `08 File System Checking_djvu.txt` | 1,316 | 7,890 |
| `09 LP Spooling System_djvu.txt` | 947 | 4,872 |
| `10 UNIX System Remote Job Entry_djvu.txt` | 1,738 | 8,261 |
| `11 UNIX System Activity Package_djvu.txt` | 537 | 3,387 |
| `12 Modification Request_djvu.txt` | 27 | 41 |
| `301-925_I1_djvu.txt` | 58,933 | 216,450 |
| `806220_djvu.txt` | 11,241 | 26,569 |
| `BSRS 104.011_djvu.txt` | 15,908 | 24,487 |
| `BSTJ_V56N10_197712_djvu.txt` | 25,898 | 121,712 |
| `BSTJ_V58N05_197905_djvu.txt` | 12,651 | 49,987 |
| `BSTJ_V60N08_198110_djvu.txt` | 20,359 | 100,161 |
| `BSTJ_V61N04_198204_djvu.txt` | 21,077 | 97,998 |
| `Crossbar-Dial-System_Section-III_Part-2-Terminating-Circuits_djvu.txt` | 22,714 | 36,392 |
| `Engineering_and_Operations_in_the_Bell_System_2ed_1984_djvu.txt` | 75,884 | 290,608 |
| `Image071317211624_djvu.txt` | 4,578 | 11,373 |
| `Image092317124839_djvu.txt` | 3,707 | 12,349 |
| `Image092317125247_djvu.txt` | 4,551 | 16,747 |
| `SD_26030-01_djvu.txt` | 12,345 | 17,731 |
| `Telecommunications_Transmission_Engineering_Vol_1_Principles_2ed_1977_djvu.txt` | 51,506 | 197,647 |
| `Telecommunications_Transmission_Engineering_Vol_2_Facilities_1ed_1977_djvu.txt` | 59,156 | 237,641 |
| `Telecommunications_Transmission_Engineering_Vol_3_2ed_1977_djvu.txt` | 55,308 | 195,939 |
| `UNIX System User's Manual, System V (Release 1)_djvu.txt` | 58,098 | 221,177 |
| `WE_Fundamentals_of_Telephony_Lesson_1_Mar62_nicer_djvu.txt` | 18,351 | 31,004 |
| `bellsystem_SD-1C900-01_djvu.txt` | 273,678 | 205,429 |
| `bstj50-7-2085_djvu.txt` | 5,485 | 17,841 |
| `bstj57-10-3371_djvu.txt` | 5,851 | 21,336 |
| `bstj57-10-3455_djvu.txt` | 4,850 | 15,161 |
| `bstj57-6-1897_djvu.txt` | 3,136 | 8,314 |
| `bstj57-6-1899_djvu.txt` | 3,319 | 9,626 |
| `bstj57-6-1971_djvu.txt` | 4,290 | 13,045 |
| `bstj57-6-2049_djvu.txt` | 5,153 | 21,163 |
| `bstj57-6-2103_djvu.txt` | 3,756 | 11,543 |
| `bstj57-6-2115_djvu.txt` | 4,259 | 15,326 |
| `bstj57-6-2155_djvu.txt` | 4,314 | 15,274 |
| `bstj57-6-2177_djvu.txt` | 4,518 | 16,496 |
| `bstj57-6-2233_djvu.txt` | 3,817 | 12,983 |
| `bstj58-6-1347_djvu.txt` | 4,180 | 10,424 |
| `bstj59-4-501_djvu.txt` | 5,128 | 17,408 |
| `bstj59-9-1757_djvu.txt` | 3,539 | 11,548 |
| `bstj59-9-1793_djvu.txt` | 4,118 | 14,524 |
| `bstj59-9-1811_djvu.txt` | 3,931 | 13,108 |
| `bstj61-6-981_djvu.txt` | 6,548 | 15,278 |
| `bstj61-7-1589_djvu.txt` | 3,929 | 10,839 |
| `bstj61-9-2459_djvu.txt` | 3,981 | 13,072 |
| `bstj62-10-2911_djvu.txt` | 4,940 | 15,920 |
| `bstj62-3-765_djvu.txt` | 4,174 | 11,094 |
| `bstj62-7-2127_djvu.txt` | 4,792 | 14,807 |
| `bstj62-7-2345_djvu.txt` | 6,327 | 16,103 |
| `cman74_djvu.txt` | 6,299 | 19,296 |
| `cman_djvu.txt` | 5,463 | 19,759 |
| `reader_djvu.txt` | 18,463 | 50,457 |

## Sourced from outside this repository

Some of what the simulation depicts is not in any document here. Where that
is so, the module says where it came from and what it will not claim. This
is the index of those.

| Claim | Where it is used | What it rests on |
| --- | --- | --- |
| Exchange cable is built in binder groups of 25 pairs, each binder taking the colours of the pair with its own number; 24 groups make 600 pairs and violet-slate is never used as a binder | `src/bell_system/cable.py` | The 25-pair colour code, published widely and consistently across telephony references |
| Cable is pressurised with dry air to keep water out, and pressure falls before water enters | `src/bell_system/cable.py` | Outside plant air pressure practice |
| RFC 850 (June 1983) header set, order, `.UUCP` site suffix, full day name in `Date`, and reply-format `Path` lines required until 1 January 1984 | `src/bell_system/filesystem.py` netnews spool | RFC 850 itself, including its worked example, from which the relay sites cbosgd, mhuxj, mhuxt and eagle are taken |
| The August 1983 AT&T strike: 7-28 August, and a settlement of 5.5 per cent in the first year and 1.5 in each of the next two | `net.misc/88` in the netnews spool | Published accounts of the strike |
| The 1956 consent decree kept AT&T out of the computer business; the 1982 decree let it in, which is why System V arrived commercially | `net.unix-wizards/121`, `/usr/doc/why.unix` | Published antitrust history, consistent with Engineering and Operations on divestiture |
| Ritchie and Thompson, CACM 17(7), July 1974, 365-375; Thompson and Bourne in BSTJ 57(6) part 2, July-August 1978, at 1931-1946 and 1971-1990; Feldman on make in SP&E 9(4), April 1979, 255-265; Kernighan on pic in SP&E 12(1), January 1982, 1-21 | `/usr/dict/papers`, read by `refer(1)` | Each citation checked against the publication record |
| Teletype Model 33 at 110 baud, ten characters a second; Model 43 (1977) switchable to 110 or 300, ten or thirty | `display.pacing` in `src/bell_system/settings.py` and `terminal.py` | Teletype Corporation specifications. The eleven-bit frame at 110 and ten above it is what makes those published character rates come out right |
| ANAC reads back the calling number; a 102-type line is a milliwatt supply at 1004 Hz and 0 dBm; a 100-type line is a quiet termination; a loop around is a pair of numbers, one toned and one silent | `src/bell_system/data/testlines.py` | Plant test number practice. The dialable codes are **not** claimed: they were local to each office, and the module says so |
| Western Electric equipment in-service years (302, 500, 1500, 2500, 1A2, No. 1 and No. 5 crossbar, 1ESS, 1AESS, 4ESS, 5ESS, T1, D4, L4, TD-2, TH-3) | `src/bell_system/screens/plant.py` | Published Bell System equipment history. Anything the sources consulted did not settle is absent from the table rather than guessed at |

| The divestiture assignment: twenty-one wholly owned operating companies, two AT&T held a minority of (SNET, Cincinnati Bell), Nevada Bell wholly owned by Pacific Telephone, four Chesapeake and Potomac companies, and the Pacific Telesis / Ameritech / Bell Atlantic groupings in full | `src/bell_system/data/companies.py`, `company(1)` | Engineering and Operations in the Bell System, 2nd ed. 1984, figure 1-9 and the surrounding text — quoted in the module |
| The NYNEX, BellSouth, Southwestern Bell and US West groupings | the same table | Externally sourced; the book's OCR of figure 1-9 gives only three groupings in full. Each is marked `verified=False` and prints a `?` in `company all` |

### What was looked for and not found

Recorded so that nobody repeats the search, and so that nothing was
invented to fill the gap:

- **The daily weather over northern New Jersey on 14 November 1983.** Every
  archive reachable from here was blocked. `src/bell_system/weather.py`
  therefore generates the shift's conditions and states plainly that no
  claim is made about what really happened that day.
- **The customer-facing report categories a repair service attendant chose
  from.** Most likely a division 660 practice, not reachable. The electrical
  faults are documented; `REPORT_SYMPTOMS` is the simulation's own
  plain-language wrapping and is marked as such.
- **COSMOS transaction syntax.** Not reproduced from any source; the
  `cosmos` subcommands are the simulation's own and the screen says so.
- **A wire centre's actual field force size.** No source consulted fixes a
  number, so `src/bell_system/field.py` uses five as a working figure and
  says why.
- **Documented differences in equipment mix between operating companies.**
  The roadmap asked for per-company character drawn from these. Neither the
  bundled documents nor anything reachable from here establishes how one
  operating company's crossbar-to-ESS mix differed from another's.
  `data/companies.py` says so, and uses the divestiture assignment instead
  — which is documented, and is what people in those buildings actually
  knew about their own company in November 1983.

## What does not ship

Two categories were removed from the working tree. Both are recoverable;
neither is needed to run, test or develop the simulation.

### The NANPA geographic dump

`full_dataset_csv.csv` was a 46 MB modern extract of North American numbering
plan data. The simulation now ships a distilled 42 KB dataset built from it,
at `src/bell_system/data/nanpa.csv.gz`, carrying only the six columns the
code reads and only area codes that could have existed in the period.

To rebuild it you need the dump. Any current NANPA-derived extract with the
columns `npa, nxx, city, state, country, latitude, longitude` will do; place
it at `attached_assets/full_dataset_csv.csv` and run:

```
python tools/build_nanpa.py
```

The build script documents the period filter and the eighteen area codes
excluded by name for postdating the simulation.

### Scanned PDFs

| Document | Size |
| --- | ---: |
| `325-048_i9_Nov82_SSM_Station_Service_Manual_vI_tci_ocr_r.pdf` | 25.2 MB |
| `42397-5ess.pdf` | 0.3 MB |
| `Bell-System-Technical-Journal-1976-3.pdf` | 1.9 MB |
| `BellLabs_v7vol2a.pdf` | 1.3 MB |
| `Documents_for_the_PWB_UNIX_Time-Sharing_System_Edition_1.0_197710.pdf` | 46.3 MB |
| `PWB_UNIX_Edition_1_Section_1_May77.pdf` | 11.5 MB |
| `UNIX_ProgrammersManual_Nov71.pdf` | 6.8 MB |
| `UNIX_Programmers_Manual_Seventh_Edition_January_1979_Volume_1_SRI_Reprint_June_1980.pdf` | 30.0 MB |
| `bell_system_80_series.pdf` | 2.4 MB |

9 files, 126 MB total.

These are page scans. No line of code cites any of them, because they are
images rather than searchable text - every verifiable claim in this project
rests on the `.txt` files above.

They were removed from the git history as well as the working tree, which
took a clone from 126.33 MiB to 6.21 MiB. Every commit is otherwise
unchanged: the rewrite was verified file by file, and all 119 files present
at the previous `main` and all 149 at the branch tip are byte-identical
before and after. They were reference reading during the
historical accuracy work and are not needed to build or run anything.

Scans of this material are held by the Internet Archive and by bitsavers,
which is where copies of these particular files came from. Exact per-file
provenance was not recorded when they were first added to the repository, so
the titles above are the reliable identifier rather than any URL this file
could offer.

## The discipline

Four rules held through the audit and the work that followed:

1. **Provenance or admission.** A value is repo-verified, externally sourced,
   or explicitly marked as the simulation's own. Where a source could not be
   reached, the gap is recorded in the source code rather than filled with
   plausible invention.
2. **Conflicts are recorded, not resolved silently.** Where two sources
   disagree - CLLI code length, what MLT stands for - both readings and the
   choice are written down.
3. **Derived is not quoted.** Figures computed from a document say so. The
   loop resistance per mile is derived from "1300 ohms, typically about three
   miles"; it is not a figure any document states.
4. **Externally sourced is labelled.** The eighteen post-period area codes in
   `tools/build_nanpa.py` come from the published history of the numbering
   plan, not from any document here, and each carries its year and parent
   code so a wrong one can be found.
