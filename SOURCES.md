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

| File | Size |
| --- | ---: |
| `00 Frontmatter and Table of Contents_djvu.txt` | 0.0 MB |
| `01 Introduction_djvu.txt` | 0.0 MB |
| `01 UNIX Documentation Road Map_djvu.txt` | 0.0 MB |
| `02 Administrative Advice (DEC)_djvu.txt` | 0.0 MB |
| `02 Editor Tutorial_djvu.txt` | 0.0 MB |
| `03 Administrative Advice (3B20S)_djvu.txt` | 0.0 MB |
| `03 UNIX for Beginners_djvu.txt` | 0.1 MB |
| `04 Setting Up The UNIX System (DEC)_djvu.txt` | 0.1 MB |
| `04 UNIX Shell Tutorial_djvu.txt` | 0.1 MB |
| `05 C Reference Manual_djvu.txt` | 0.1 MB |
| `05 Setting Up The UNIX System (3B20)_djvu.txt` | 0.1 MB |
| `06 Auto Call Facility Installation_djvu.txt` | 0.0 MB |
| `06 UNIX Programming_djvu.txt` | 0.1 MB |
| `07 UNIX System Accounting_djvu.txt` | 0.0 MB |
| `08 File System Checking_djvu.txt` | 0.0 MB |
| `09 LP Spooling System_djvu.txt` | 0.0 MB |
| `10 UNIX System Remote Job Entry_djvu.txt` | 0.1 MB |
| `11 UNIX System Activity Package_djvu.txt` | 0.0 MB |
| `12 Modification Request_djvu.txt` | 0.0 MB |
| `301-925_I1_djvu.txt` | 1.4 MB |
| `806220_djvu.txt` | 0.3 MB |
| `BSRS 104.011_djvu.txt` | 0.3 MB |
| `BSTJ_V56N10_197712_djvu.txt` | 0.9 MB |
| `BSTJ_V58N05_197905_djvu.txt` | 0.4 MB |
| `BSTJ_V60N08_198110_djvu.txt` | 0.7 MB |
| `BSTJ_V61N04_198204_djvu.txt` | 0.7 MB |
| `Crossbar-Dial-System_Section-III_Part-2-Terminating-Circuits_djvu.txt` | 0.3 MB |
| `Engineering_and_Operations_in_the_Bell_System_2ed_1984_djvu.txt` | 2.1 MB |
| `Image071317211624_djvu.txt` | 0.2 MB |
| `Image092317124839_djvu.txt` | 0.2 MB |
| `Image092317125247_djvu.txt` | 0.2 MB |
| `SD_26030-01_djvu.txt` | 0.2 MB |
| `Telecommunications_Transmission_Engineering_Vol_1_Principles_2ed_1977_djvu.txt` | 1.4 MB |
| `Telecommunications_Transmission_Engineering_Vol_2_Facilities_1ed_1977_djvu.txt` | 1.7 MB |
| `Telecommunications_Transmission_Engineering_Vol_3_2ed_1977_djvu.txt` | 1.4 MB |
| `UNIX System User's Manual, System V (Release 1)_djvu.txt` | 1.5 MB |
| `WE_Fundamentals_of_Telephony_Lesson_1_Mar62_nicer_djvu.txt` | 0.3 MB |
| `bellsystem_SD-1C900-01_djvu.txt` | 1.5 MB |
| `bstj50-7-2085_djvu.txt` | 0.2 MB |
| `bstj57-10-3371_djvu.txt` | 0.2 MB |
| `bstj57-10-3455_djvu.txt` | 0.2 MB |
| `bstj57-6-1897_djvu.txt` | 0.2 MB |
| `bstj57-6-1899_djvu.txt` | 0.2 MB |
| `bstj57-6-1971_djvu.txt` | 0.2 MB |
| `bstj57-6-2049_djvu.txt` | 0.2 MB |
| `bstj57-6-2103_djvu.txt` | 0.2 MB |
| `bstj57-6-2115_djvu.txt` | 0.2 MB |
| `bstj57-6-2155_djvu.txt` | 0.2 MB |
| `bstj57-6-2177_djvu.txt` | 0.2 MB |
| `bstj57-6-2233_djvu.txt` | 0.2 MB |
| `bstj58-6-1347_djvu.txt` | 0.2 MB |
| `bstj59-4-501_djvu.txt` | 0.2 MB |
| `bstj59-9-1757_djvu.txt` | 0.2 MB |
| `bstj59-9-1793_djvu.txt` | 0.2 MB |
| `bstj59-9-1811_djvu.txt` | 0.2 MB |
| `bstj61-6-981_djvu.txt` | 0.2 MB |
| `bstj61-7-1589_djvu.txt` | 0.2 MB |
| `bstj61-9-2459_djvu.txt` | 0.2 MB |
| `bstj62-10-2911_djvu.txt` | 0.2 MB |
| `bstj62-3-765_djvu.txt` | 0.2 MB |
| `bstj62-7-2127_djvu.txt` | 0.2 MB |
| `bstj62-7-2345_djvu.txt` | 0.2 MB |
| `cman74_djvu.txt` | 0.2 MB |
| `cman_djvu.txt` | 0.2 MB |
| `reader_djvu.txt` | 0.4 MB |

65 files, 22 MB total.

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
rests on the `.txt` files above. They were reference reading during the
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
