# Critères de Détection - xAI PDF Converter

## Vue d'Ensemble

Le système détecte **27 types d'informations sensibles** dans les documents PDF SEC avec des critères très stricts pour minimiser les faux positifs.

---

## 📧 1. EMAIL

### Pattern
```regex
\b[a-zA-Z0-9][a-zA-Z0-9._%+-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}\b
```

### Critères
- Doit commencer par une lettre ou un chiffre
- Peut contenir: lettres, chiffres, `.`, `_`, `%`, `+`, `-`
- Le `@` est obligatoire
- Domaine avec au moins 2 caractères après le point

### Exemples
✅ `john.smith@company.com`
✅ `investor_relations@vantiv.com`
❌ `@company.com` (pas de partie locale)
❌ `john@c` (domaine trop court)

---

## 📞 2. PHONE NUMBER

### Pattern 1: US Format
```regex
\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b
```

### Pattern 2: International Format
- `+XX (0) XXXX XXXX XXXX`
- `+XX XXXX XXXX XXXX`
- `00XX XXXX XXXX XXXX`
- `(0) XX XXXX XXXX`

### Pattern 3: Avec Extension
```regex
\+\d{1,3}\s+\d{1,4}\s+\d{3,4}\s+\d{3,4}\s+(?:ext|x|extension)\.?\s*\d{1,5}
```

### Critères de Validation
- **Doit avoir un contexte positif** dans les 200 caractères avant/après:
  - `phone`, `tel`, `telephone`, `call`, `fax`, `contact`
- **Rejeté si contexte négatif**:
  - `file number`, `CIK`, `case`, `docket`, `exhibit`, `schedule`

### Exemples
✅ `Phone: (513) 900-5250`
✅ `+1 513 900 5250`
✅ `Tel: 513-900-5250 ext. 123`
❌ `513-900-5250` (sans contexte)
❌ `File Number: 333-12345` (contexte négatif)

---

## 🏠 3. ADDRESS / PARTIAL ADDRESS

### Address Pattern (Complète)
```regex
\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Circle|Cir|Place|Pl)
```

### Partial Address Pattern
- Ville + État + ZIP: `City, ST 12345`
- ZIP code seul: `12345` ou `12345-6789`

### Critères de Validation
- **Adresse complète**: Numéro + Nom de rue + Type de voie
- **Adresse partielle**: Ville, État, ZIP avec contexte
- **Minimum 5 caractères**
- **Context window**: 100 caractères avant/après

### Exemples
✅ `8500 Governors Hill Drive`
✅ `Cincinnati, OH 45249`
✅ `Edgewood, NY 11717`
❌ `123` (trop court)
❌ `Main Street` (pas de numéro)

---

## 💳 4. SSN (Social Security Number)

### Pattern
```regex
\b\d{3}-\d{2}-\d{4}\b
```

### Critères
- Format exact: `XXX-XX-XXXX`
- **Contexte obligatoire** (50 caractères avant/après):
  - `SSN`, `social security`, `tax ID`, `identification`

### Exemples
✅ `SSN: 123-45-6789`
❌ `123-45-6789` (sans contexte)

---

## 🏦 5. IRS EIN (Employer Identification Number)

### Pattern
```regex
\b\d{2}-\d{7,8}\b
```

### Critères
- Format: `XX-XXXXXXX` ou `XX-XXXXXXXX`
- **Contexte obligatoire**:
  - `EIN`, `employer identification`, `tax ID`, `IRS`, `federal tax`

### Exemples
✅ `EIN: 31-1368535`
✅ `Federal Tax ID: 31-1368535`
❌ `31-1368535` (sans contexte)

---

## 📋 6. COMMISSION FILE NUMBER

### Pattern
```regex
Commission\s+File\s+Number[:\s]+(\d{3}-\d{5})
```

### Critères
- Format exact: `XXX-XXXXX`
- **Doit avoir le préfixe** "Commission File Number"

### Exemples
✅ `Commission File Number: 001-35462`
❌ `001-35462` (sans préfixe)

---

## 🔢 7. CIK NUMBER (SEC Central Index Key)

### Pattern 1: Avec Contexte
```regex
CIK\s*(?:Number|No\.?)?\s*[:#]?\s*(\d{7,10})
```

### Pattern 2: Sans Contexte (Plus Strict)
```regex
\b\d{7,10}\b
```

### Critères de Validation (Pattern 2)
- **Contexte positif requis** (100 caractères):
  - `central index`, `registrant`, `SEC`, `filer`, `issuer`
- **Doit avoir 10 chiffres** (CIK standard)

### Exemples
✅ `CIK: 0001534675`
✅ `CIK Number 1534675`
✅ `Registrant CIK 0001534675`
❌ `1234567` (trop court)

---

## 💼 8. CUSIP CODE

### Pattern
```regex
\b([0-9A-Z]{6,9}[A-Z0-9]{2}[0-9])\b
```

### Critères
- 6-9 caractères alphanumériques
- 2 caractères alphanumériques
- 1 chiffre de contrôle
- **Total: 9-12 caractères**

### Exemples
✅ `G98239AA1`
✅ `037833100`

---

## 🌍 9. ISIN CODE

### Pattern
```regex
\b(US[0-9A-Z]{9}[0-9])\b
```

### Critères
- Commence par `US` (codes US uniquement)
- 9 caractères alphanumériques
- 1 chiffre de contrôle
- **Total: 12 caractères**

### Exemples
✅ `US0378331005`
✅ `US9128473801`

---

## 📈 10. TICKER SYMBOL

### Pattern
```regex
\((?:NYSE|NASDAQ|AMEX|OTC):\s*([A-Z]{1,5})\)
```

### Critères
- **Doit être entre parenthèses**
- **Doit avoir le nom de la bourse**: NYSE, NASDAQ, AMEX, OTC
- 1 à 5 lettres majuscules

### Exemples
✅ `(NYSE: VNTV)`
✅ `(NASDAQ: AAPL)`
❌ `VNTV` (sans parenthèses ni bourse)

---

## 👤 11. PERSON NAME

### Stratégie: 6 Patterns Différents

#### Pattern 1: Contextes de Personnes
```regex
(?:Director|Officer|Employee|Individual|Beneficial Owner|Person|Shareholder|Mr\.|Mrs\.|Ms\.|Dr\.)[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)
```

#### Pattern 2: Listes/Tableaux
```regex
([A-Z][a-z]+),\s+([A-Z][a-z]+(?:\s+[A-Z]\.?)?)
```

#### Pattern 3: Sections de Signatures
```regex
(?:Signed by|By|Name|Signature)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)
```

#### Pattern 4: Tableaux de Personnes
```regex
([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[|\-]\s*(?:CEO|CFO|President|Director)
```

#### Pattern 5: Emails
```regex
([a-z]+\.?[a-z]+)\.([a-z]+)@
```

#### Pattern 6: Détection Générale (TRÈS STRICTE)
```regex
\b([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b
```

### Nettoyage Automatique (AVANT Validation)
1. **Enlever dates/nombres**: `2/17/2026 S. Ferris` → `S. Ferris`
2. **Enlever signatures**: `/s/ John Smith` → `John Smith`
3. **Enlever parenthèses**: `Charles Drucker(7)(8` → `Charles Drucker`
4. **Enlever tirets**: `David Karnstedt - - -` → `David Karnstedt`

### Critères de Validation STRICTS
❌ **Rejeté si**:
- Contient un verbe (ending, reducing, etc.)
- Contient un possessif (our, his, their)
- Est un titre de poste seul (Chief Executive Officer)
- Est un terme financier (Annual Report, Balance Sheet)
- Est un nom d'entreprise connu
- Est dans la liste des faux positifs (400+ entrées)
- Contient des mots invalides (Company, Corporation, Inc, etc.)

✅ **Accepté si**:
- Format: Prénom + Nom (ou Initiale + Nom)
- Pas de mots interdits
- Pas de structure d'entreprise
- Contexte approprié

### Exemples
✅ `John Smith`
✅ `J. Anderson`
✅ `Michael A. Rodriguez`
✅ `Director: Sarah Williams`
❌ `Chief Executive Officer` (titre seul)
❌ `Annual Report` (faux positif)
❌ `Vantiv Inc` (entreprise)

---

## 🏢 12. EXECUTIVE NAME

### Stratégie: Détection avec Titres

#### Pattern 1: Signatures
```regex
/s[/\s]+\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?[A-Z][a-z]+)
```

#### Pattern 2: Format "Nom, Titre"
```regex
([A-Z][a-z]+(?:\s+[A-Z]\.?)?[A-Z][a-z]+),\s*(Chief|President|Director|Officer|Vice President|CEO|CFO|COO|CTO|Chairman)
```

#### Pattern 3: Format "Titre: Nom"
```regex
(Chief|President|Director|Officer|CEO|CFO)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)
```

#### Pattern 4: Sections de Signatures
```regex
(?:By|Name|Signed By|Officer)[:\s]+([A-Z][a-z]+\s+[A-Z][a-z]+)
```

#### Pattern 5: Tableaux
```regex
([A-Z][a-z]+\s+[A-Z][a-z]+)\s*[|\-]\s*(CEO|CFO|President)
```

#### Pattern 6: Sections "Officers"
Dans les sections contenant "Officers" ou "Executive Officers"

### Critères
- **Doit avoir un titre de fonction** proche du nom
- Même validation stricte que Person Name
- Même nettoyage automatique

### Exemples
✅ `/s/ Charles W. Drucker`
✅ `Jeffrey A. Stieﬂer, Chief Executive Officer`
✅ `President: John Smith`
✅ `Stephanie Ferris | CFO`

---

## 🏛️ 13. COMPANY NAME

### Stratégie: 2 Méthodes

#### Méthode 1: Contexte "Registrant"
```regex
(?:Exact name of registrant|Name of the company|Registrant)[:\s]+([A-Z][^\n]{4,60})
```

#### Méthode 2: Format Standalone
Détection de noms avec suffixes:
- `Inc.`, `LLC`, `Ltd.`, `Corporation`, `Corp.`, `Company`, `Co.`
- `LP`, `LLP`, `SA`, `SAS`, `SARL`, `GmbH`, `AG`

### Critères de Validation
- **Longueur**: 5-60 caractères
- **Maximum 6 mots**
- **Pas de verbes** dans le contexte proche
- **Pas de termes financiers** autour
- **Doit contenir un suffixe corporate** (pour méthode 2)

### Exemples
✅ `Vantiv, Inc.`
✅ `Fifth Third Bancorp`
✅ `Goldman Sachs & Co. LLC`
❌ `The Company` (trop générique)
❌ `Annual Report Inc` (faux positif)

---

## 🏦 14-17. PROFESSIONAL FIRMS

### Types Détectés

#### 14. AUDITOR (Cabinets d'Audit)
**Noms connus**:
- KPMG LLP
- Ernst & Young LLP
- Deloitte & Touche LLP
- PricewaterhouseCoopers LLP
- Grant Thornton LLP
- BDO USA LLP
- Crowe Horwath LLP

**Pattern**:
```regex
(KPMG|Ernst\s*&\s*Young|Deloitte|PricewaterhouseCoopers|Grant Thornton|BDO USA|Crowe)\s*(?:,?\s*LLP|L\.L\.P\.|LLP)?
```

#### 15. LAW FIRM (Cabinets d'Avocats)
**Critères**:
- Contient 2-4 noms propres séparés par virgules
- Se termine par `LLP`, `P.C.`, `P.A.`, etc.
- Format: `Nom1, Nom2, Nom3 & Nom4 LLP`

**Pattern**:
```regex
([A-Z][a-z]+(?:,\s*[A-Z][a-z]+){1,3}\s*&\s*[A-Z][a-z]+\s+(?:LLP|P\.C\.|P\.A\.))
```

**Exemples**:
✅ `Skadden, Arps, Slate, Meagher & Flom LLP`
✅ `Latham & Watkins LLP`

#### 16. UNDERWRITER (Banques d'Investissement)
**Noms connus**:
- Goldman Sachs & Co. LLC
- J.P. Morgan Securities LLC
- Morgan Stanley & Co. LLC
- Credit Suisse Securities (USA) LLC
- Deutsche Bank Securities Inc.

**Contexte requis**:
- `underwriter`, `lead manager`, `book runner`

#### 17. FINANCIAL INSTITUTION (Banques)
**Suffixes**:
- `Bank`, `Trust Company`, `National Bank`, `Bancorp`
- `N.A.`, `National Association`

**Contexte requis**:
- `trustee`, `agent`, `bank`, `lender`, `depositary`

**Exemples**:
✅ `U.S. Bank National Association`
✅ `The Bank of New York Mellon`
✅ `Wells Fargo Bank, N.A.`

---

## 📍 18. CITY NAME

### Pattern
```regex
([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)
```

### Critères
- **Format strict**: `Ville, État ZIP`
- État en 2 lettres majuscules
- ZIP code US valide

### Exemples
✅ `Cincinnati, OH 45249`
✅ `New York, NY 10001`
❌ `Cincinnati` (sans État/ZIP)

---

## 💼 19. PROFESSIONAL FIRM (Générique)

Détecte les firmes professionnelles non classées dans les autres catégories.

### Pattern
```regex
([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\s+(?:LLC|LLP|Inc\.|Co\.|Ltd\.|Corporation|Partners|Associates))
```

### Critères
- 1-4 noms propres
- Suffixe corporate
- Pas déjà détecté comme auditor/law firm/underwriter

---

## 📅 20. IMPORTANT DATE

### Patterns (DÉSACTIVÉ par défaut)

Si activé, détecte:
- Format texte: `December 31, 2017`
- Format numérique: `12/31/2017`, `12-31-2017`
- Format ISO: `2017-12-31`

**Note**: Désactivé car génère trop de détections (chaque date dans le document).

---

## 📝 21. QUOTED TITLE

### Pattern (DÉSACTIVÉ par défaut)

Détecte les titres entre guillemets:
```regex
[""]([A-Z][A-Za-z\s]+(?:of|is|the|and)[A-Za-z\s]+)[""]
```

**Note**: Désactivé car faible utilité.

---

## 🎯 Système Anti-Faux Positifs

### Listes de Validation

#### INVALID_NAME_WORDS (400+ entrées)
Mots qui invalident un nom de personne:
- Termes d'entreprise: `Company`, `Corporation`, `Inc`, `LLC`
- Termes financiers: `Annual Report`, `Balance Sheet`, `Cash Flow`
- Termes génériques: `The Company`, `Our Business`, `This Agreement`

#### PERSON_NAME_FALSE_POSITIVES (200+ entrées)
Faux positifs connus à rejeter:
- `Annual Report`, `Balance Sheet`, `Income Statement`
- `Chief Executive`, `Board of Directors`
- `New York`, `United States`, `Third Quarter`

#### COMPANY_NAME_KEYWORDS
Mots qui indiquent un nom d'entreprise:
- `Bank`, `Trust`, `Capital`, `Securities`, `Holdings`
- `Financial`, `Investment`, `Asset`, `Fund`, `Partners`

### Validation Contextuelle

Pour chaque détection:
1. **Nettoyer** la valeur (enlever dates, signatures, etc.)
2. **Vérifier** contre les listes de faux positifs
3. **Analyser** le contexte (50-200 caractères autour)
4. **Valider** la structure et le format
5. **Rejeter** si contexte négatif ou structure invalide

---

---

## 🔗 22. SEC.GOV URL

### Pattern
```regex
https?://(?:www\.)?sec\.gov/[^\s<>"')]+
```

### Critères
- Doit commencer par `http://` ou `https://`
- Domaine: `sec.gov` ou `www.sec.gov`
- Capture tout le chemin jusqu'à un espace ou caractère de fin

### Validation
- Retire automatiquement la ponctuation finale (`.`, `,`, `;`, `:`, `!`, `?`)
- **Aucun contexte requis** - Les URLs SEC.gov sont toujours sensibles (contiennent CIK, file numbers, etc.)

### Exemples
✅ `https://www.sec.gov/cgi-bin/browse-edgar?CIK=0001018724`
✅ `http://sec.gov/Archives/edgar/data/1018724/000119312517065791/d293630d10k.htm`
✅ `https://www.sec.gov/files/form10-k.pdf`
❌ `http://www.example.com/sec.gov/fake` (domaine différent)

---

## 🇬🇧 23. SEDOL CODE (UK Securities)

### Pattern
```regex
\b[0-9BCDFGHJKLMNPQRSTVWXYZ]{7}\b
```

### Critères
- **7 caractères** exactement
- Alphanumériques (chiffres + consonnes uniquement, **pas de voyelles AEIOU**)
- Format: 6 caractères + 1 chiffre de contrôle

### Validation Contexte
- **Contexte requis** (60 caractères avant/après):
  - Doit contenir: `SEDOL`, `UK SECURITY`, ou `LONDON STOCK`

### Exemples
✅ `2046251` (context: "SEDOL: 2046251")
✅ `B0WNLY7` (context: "UK Security SEDOL B0WNLY7")
❌ `ABCDEFG` (contient des voyelles)
❌ `1234567` (sans contexte SEDOL)

---

## 📊 24. FIGI CODE (Bloomberg Identifiers)

### Pattern
```regex
\bBBG[0-9A-Z]{9}\b
```

### Critères
- **Format strict**: `BBG` + 9 caractères alphanumériques
- Total: **12 caractères** exactement
- Base 36 encoding (0-9, A-Z)

### Validation
- **Aucun contexte requis** - Le préfixe `BBG` rend le format unique
- Toujours en majuscules

### Exemples
✅ `BBG000BLNQ16` (Apple Inc.)
✅ `BBG000BPH459` (Alphabet Inc.)
✅ `BBG000BVPV84` (Amazon.com Inc.)
❌ `BBG123` (trop court)
❌ `bbg000blnq16` (minuscules - invalide)

---

## 🏛️ 25. LEI CODE (Legal Entity Identifier)

### Pattern
```regex
\b[A-Z0-9]{20}\b
```

### Critères
- **20 caractères** alphanumériques exactement
- Structure: 4-char LOU ID + 2 reserved + 12-char entity ID + 2-char checksum
- **Toujours en majuscules**

### Validation Contexte (TRÈS STRICTE)
- **Contexte requis** (80 caractères avant/après):
  - Doit contenir: `LEI`, `LEGAL ENTITY IDENTIFIER`, ou `ENTITY IDENTIFIER CODE`
- Validation supplémentaire:
  - `.isupper()` - Doit être tout en majuscules
  - `.isalnum()` - Doit être alphanumériques uniquement

### Exemples
✅ `549300VGEJKB7SVUZR78` (context: "LEI: 549300VGEJKB7SVUZR78")
✅ `213800WAVVOPS85N2205` (context: "Legal Entity Identifier 213800WAVVOPS85N2205")
❌ `549300vgejkb7svuzr78` (minuscules - invalide)
❌ `12345678901234567890` (sans contexte LEI - trop de faux positifs)

**Note**: Sans contexte strict, le risque de faux positifs est **très élevé** (toute chaîne de 20 caractères alphanumériques serait détectée).

---

## 🌍 26. ISIN CODE - EXPANDED (All Countries)

### Pattern Original (US uniquement)
```regex
\b(US[0-9A-Z]{9}[0-9])\b
```

### Pattern Étendu (Tous pays)
```regex
\b([A-Z]{2}[A-Z0-9]{9}[0-9])\b
```

### Critères
- **12 caractères** exactement
- Structure:
  - 2 lettres: code pays ISO (US, GB, DE, FR, JP, etc.)
  - 9 caractères: identifiant national (alphanumériques)
  - 1 chiffre: checksum (validation Luhn modulo 10)

### Validation
- **US ISINs**: Pas de contexte requis (détectés automatiquement)
- **Non-US ISINs**: Contexte requis (60 caractères):
  - Doit contenir: `ISIN`, `INTERNATIONAL SECURITIES`, ou `SECURITY IDENTIFIER`

### Exemples
✅ `US0378331005` (Apple Inc. - US)
✅ `GB0002374006` (Vodafone Group - UK, avec contexte "ISIN")
✅ `DE0005140008` (Deutsche Bank - Germany, avec contexte)
✅ `FR0000120271` (Total SE - France, avec contexte)
❌ `XX1234567890` (code pays invalide)
❌ `GB00023740061` (trop long - 13 caractères)

---

## 🔬 27. PATENT NUMBER (US Patents)

### Pattern
```regex
\bUS\d{7,8}[A-Z]?\d?\b
```

### Critères
- **Format**: `US` + 7-8 chiffres + (optionnel) lettre + (optionnel) chiffre
- Structure:
  - Préfixe: `US` (obligatoire)
  - Numéro: 7 ou 8 chiffres
  - Type (optionnel): Lettre (A, B, C, etc.)
  - Révision (optionnelle): Chiffre (1, 2, etc.)

### Validation Contexte
- **Contexte requis** (80 caractères avant/après):
  - Doit contenir: `PATENT`, `PATENT NO`, `PATENT NUMBER`, `U.S. PATENT`, `ISSUED`, `INTELLECTUAL PROPERTY`, ou `IP PORTFOLIO`

### Exemples
✅ `US1234567` (context: "Patent No. US1234567")
✅ `US12345678A` (context: "U.S. Patent US12345678A")
✅ `US7654321B2` (context: "Issued Patent: US7654321B2")
❌ `US123` (trop court - < 7 chiffres)
❌ `US12345678` (sans contexte "Patent")

---

## 📊 Résumé des Types

| # | Type | Pattern | Contexte Requis | Validation |
|---|------|---------|----------------|------------|
| 1 | Email | Regex strict | Non | Format |
| 2 | Phone | 3 patterns | **Oui** | Contexte + Format |
| 3 | Address | Street pattern | Partiel | Format + Longueur |
| 4 | SSN | XXX-XX-XXXX | **Oui** | Contexte |
| 5 | IRS EIN | XX-XXXXXXXX | **Oui** | Contexte |
| 6 | Commission File # | XXX-XXXXX | **Oui** (préfixe) | Préfixe obligatoire |
| 7 | CIK | 7-10 chiffres | Partiel | Contexte + Longueur |
| 8 | CUSIP | 9-12 chars | Non | Format |
| 9 | ISIN | US + 10 chars | Non | Format |
| 10 | Ticker | (NYSE: XXX) | **Oui** (parenthèses) | Format strict |
| 11 | Person Name | 6 patterns | Partiel | **TRÈS STRICTE** |
| 12 | Executive Name | 6 patterns | **Oui** (titre) | Stricte + Titre |
| 13 | Company Name | 2 méthodes | Partiel | Suffixe + Validation |
| 14 | Auditor | Noms connus | Non | Liste prédéfinie |
| 15 | Law Firm | Pattern LLP | Non | Format + Suffixe |
| 16 | Underwriter | Noms connus | **Oui** | Liste + Contexte |
| 17 | Financial Institution | Bank/Trust | **Oui** | Suffixe + Contexte |
| 18 | City Name | Ville, ST ZIP | **Oui** | Format strict |
| 19 | Professional Firm | Pattern générique | Non | Suffixe |
| 20 | Important Date | 3 formats | Non | (Désactivé) |
| 21 | Quoted Title | Guillemets | Non | (Désactivé) |
| 22 | SEC.gov URL | https://sec.gov/* | Non | Format domaine |
| 23 | SEDOL Code | 7 chars (consonnes) | **Oui** | Contexte + Format |
| 24 | FIGI Code | BBG + 9 chars | Non | Préfixe unique |
| 25 | LEI Code | 20 chars uppercase | **Oui** (STRICT) | Contexte + Uppercase |
| 26 | ISIN Expanded | 2-letter + 10 chars | Partiel (non-US) | Format + Contexte |
| 27 | Patent Number | US + 7-8 digits | **Oui** | Contexte + Format |

---

**© 2025 Conrad Vaslin - xAI Finance Tutor**

*Détection ultra-stricte pour minimiser les faux positifs dans les documents SEC*
