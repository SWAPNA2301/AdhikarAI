# Retrieval evaluation — DRAFT

Gold labels are DRAFT and require human review. These measure retrieval relevance, not eligibility.

Run (UTC): 2026-11-18T16:32:48.458219+00:00. Queries: 40; schemes: 10. Encoder: sentence-transformers/all-MiniLM-L6-v2. Cosine-distance cutoff: 0.82. Recipe: mean-token-windows-cosine-v1.

Query SHA-256: `400fc1251ec37c1406933a56523c89aeaf8f6f0c2d9e7ffd042b6e2a06d809bd`. Dataset SHA-256: `fc9b852879341b9a46da4e9c0bfdb16cf4d064358f0346d80d71b744bed0160e`.

Recall@k is macro-averaged over queries with nonempty gold lists: retrieved gold IDs / all gold IDs.
MRR uses the first relevant result in the full returned scheme ranking (after the existing cutoff).
Empty-gold queries are excluded from recall and MRR; no-match accuracy measures their empty-result rate.
Keyword ties retain dataset order. Both methods use schemes only, no PDF chunks or taxonomy filters.

| Method | Recall@1 | Recall@3 | Recall@5 | MRR | No-match accuracy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Keyword | 0.3810 | 0.4286 | 0.4286 | 0.4143 | 1.0000 |
| Semantic | 0.6238 | 0.8429 | 0.9000 | 0.8357 | 0.4000 |

## Per-query results and misses

Missing gold IDs are reported separately at each cutoff. For empty gold, any returned ID is a false positive.

| # | Method | Query | Language | Gold | Ranked results (full) | Misses@1 | Misses@3 | Misses@5 | No-match outcome |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Keyword | Pradhan Mantri Suraksha Bima Yojana | en | IN-PMSBY | IN-PMSBY | — | — | — | — |
| 2 | Keyword | Pradhan Mantri Jeevan Jyoti Bima Yojana | en | IN-PMJJBY | IN-PMJJBY | — | — | — | — |
| 3 | Keyword | Atal Pension Yojana | en | IN-APY | IN-APY | — | — | — | — |
| 4 | Keyword | Pradhan Mantri Shram Yogi Maandhan | en | IN-PM-SYM | IN-PM-SYM | — | — | — | — |
| 5 | Keyword | Pradhan Mantri Kisan Samman Nidhi | en | IN-PM-KISAN | IN-PM-KISAN | — | — | — | — |
| 6 | Keyword | Lakshmir Bhandar | en | IN-WB-LAKSHMIR-BHANDAR | IN-WB-LAKSHMIR-BHANDAR | — | — | — | — |
| 7 | Keyword | Kanyashree Prakalpa | en | IN-WB-KANYASHREE | IN-WB-KANYASHREE | — | — | — | — |
| 8 | Keyword | Rupashree Prakalpa | en | IN-WB-RUPASHREE | IN-WB-RUPASHREE | — | — | — | — |
| 9 | Keyword | Krishak Bandhu | en | IN-WB-KRISHAK-BANDHU | IN-WB-KRISHAK-BANDHU | — | — | — | — |
| 10 | Keyword | Swasthya Sathi | en | IN-WB-SWASTHYA-SATHI | IN-WB-LAKSHMIR-BHANDAR, IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | — | — | — |
| 11 | Keyword | I need low cost insurance if an accident leaves me disabled | en | IN-PMSBY | ∅ | IN-PMSBY | IN-PMSBY | IN-PMSBY | — |
| 12 | Keyword | Life insurance to support my family if I die | en | IN-PMJJBY | ∅ | IN-PMJJBY | IN-PMJJBY | IN-PMJJBY | — |
| 13 | Keyword | I want to contribute now for a monthly pension after sixty | en | IN-APY, IN-PM-SYM | ∅ | IN-APY, IN-PM-SYM | IN-APY, IN-PM-SYM | IN-APY, IN-PM-SYM | — |
| 14 | Keyword | I am a street vendor looking for a retirement pension | en | IN-PM-SYM, IN-APY | ∅ | IN-PM-SYM, IN-APY | IN-PM-SYM, IN-APY | IN-PM-SYM, IN-APY | — |
| 15 | Keyword | Income support for a farmer who owns agricultural land | en | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | ∅ | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | — |
| 16 | Keyword | Monthly financial assistance for women in West Bengal | en | IN-WB-LAKSHMIR-BHANDAR | ∅ | IN-WB-LAKSHMIR-BHANDAR | IN-WB-LAKSHMIR-BHANDAR | IN-WB-LAKSHMIR-BHANDAR | — |
| 17 | Keyword | money for my daughter's education | en | IN-WB-KANYASHREE | ∅ | IN-WB-KANYASHREE | IN-WB-KANYASHREE | IN-WB-KANYASHREE | — |
| 18 | Keyword | My daughter is getting married and we need financial assistance | en | IN-WB-RUPASHREE | ∅ | IN-WB-RUPASHREE | IN-WB-RUPASHREE | IN-WB-RUPASHREE | — |
| 19 | Keyword | Help for a farming family in Bengal after the farmer dies | en | IN-WB-KRISHAK-BANDHU | ∅ | IN-WB-KRISHAK-BANDHU | IN-WB-KRISHAK-BANDHU | IN-WB-KRISHAK-BANDHU | — |
| 20 | Keyword | Cashless hospital treatment for my family in West Bengal | en | IN-WB-SWASTHYA-SATHI | ∅ | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | — |
| 21 | Keyword | Insurance for accidental death through my bank account | en | IN-PMSBY | ∅ | IN-PMSBY | IN-PMSBY | IN-PMSBY | — |
| 22 | Keyword | Bank account life cover with an annual premium | en | IN-PMJJBY | IN-PMJJBY | — | — | — | — |
| 23 | Keyword | I work as a domestic helper and earn little, can I save for retirement | en | IN-PM-SYM, IN-APY | ∅ | IN-PM-SYM, IN-APY | IN-PM-SYM, IN-APY | IN-PM-SYM, IN-APY | — |
| 24 | Keyword | A grant to help an unmarried girl stay in school in Bengal | en | IN-WB-KANYASHREE | ∅ | IN-WB-KANYASHREE | IN-WB-KANYASHREE | IN-WB-KANYASHREE | — |
| 25 | Keyword | Support for a woman's first marriage in West Bengal | en | IN-WB-RUPASHREE | ∅ | IN-WB-RUPASHREE | IN-WB-RUPASHREE | IN-WB-RUPASHREE | — |
| 26 | Keyword | West Bengal financial help for cultivating my farm | en | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | ∅ | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | — |
| 27 | Keyword | I need help paying hospital bills | en | IN-WB-SWASTHYA-SATHI | ∅ | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | — |
| 28 | Keyword | Help with retirement | en | IN-APY, IN-PM-SYM | ∅ | IN-APY, IN-PM-SYM | IN-APY, IN-PM-SYM | IN-APY, IN-PM-SYM | — |
| 29 | Keyword | Help for farmers | en | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | ∅ | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | — |
| 30 | Keyword | Support for girls | en | IN-WB-KANYASHREE, IN-WB-RUPASHREE | ∅ | IN-WB-KANYASHREE, IN-WB-RUPASHREE | IN-WB-KANYASHREE, IN-WB-RUPASHREE | IN-WB-KANYASHREE, IN-WB-RUPASHREE | — |
| 31 | Keyword | Insurance | en | IN-PMSBY, IN-PMJJBY, IN-WB-SWASTHYA-SATHI | IN-PMSBY, IN-PMJJBY, IN-WB-SWASTHYA-SATHI | IN-PMJJBY, IN-WB-SWASTHYA-SATHI | — | — | — |
| 32 | Keyword | Help for women | en | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | ∅ | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | — |
| 33 | Keyword | School assistance | en | IN-WB-KANYASHREE | IN-WB-KANYASHREE, IN-WB-RUPASHREE | — | — | — | — |
| 34 | Keyword | Marriage support | en | IN-WB-RUPASHREE | IN-WB-RUPASHREE | — | — | — | — |
| 35 | Keyword | Health cover | en | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | — | — | — | — |
| 36 | Keyword | How do I renew my passport | en | ∅ | ∅ | — | — | — | correct abstention |
| 37 | Keyword | Subsidy for installing solar panels on my rooftop | en | ∅ | ∅ | — | — | — | correct abstention |
| 38 | Keyword | Education loan for a master's degree abroad | en | ∅ | ∅ | — | — | — | correct abstention |
| 39 | Keyword | How can I repair my laptop screen | en | ∅ | ∅ | — | — | — | correct abstention |
| 40 | Keyword | Unemployment allowance for a software engineer | en | ∅ | ∅ | — | — | — | correct abstention |
| 1 | Semantic | Pradhan Mantri Suraksha Bima Yojana | en | IN-PMSBY | IN-PM-SYM, IN-PMSBY, IN-PMJJBY, IN-WB-LAKSHMIR-BHANDAR, IN-APY, IN-PM-KISAN, IN-WB-KANYASHREE, IN-WB-SWASTHYA-SATHI, IN-WB-RUPASHREE, IN-WB-KRISHAK-BANDHU | IN-PMSBY | — | — | — |
| 2 | Semantic | Pradhan Mantri Jeevan Jyoti Bima Yojana | en | IN-PMJJBY | IN-PM-SYM, IN-PMJJBY, IN-PMSBY, IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-SWASTHYA-SATHI, IN-PM-KISAN, IN-APY, IN-WB-RUPASHREE, IN-WB-KRISHAK-BANDHU | IN-PMJJBY | — | — | — |
| 3 | Semantic | Atal Pension Yojana | en | IN-APY | IN-APY, IN-PM-SYM, IN-PMSBY, IN-PM-KISAN, IN-PMJJBY, IN-WB-KRISHAK-BANDHU, IN-WB-LAKSHMIR-BHANDAR, IN-WB-SWASTHYA-SATHI, IN-WB-KANYASHREE, IN-WB-RUPASHREE | — | — | — | — |
| 4 | Semantic | Pradhan Mantri Shram Yogi Maandhan | en | IN-PM-SYM | IN-PM-SYM, IN-PMSBY, IN-WB-LAKSHMIR-BHANDAR, IN-PMJJBY, IN-PM-KISAN, IN-WB-SWASTHYA-SATHI, IN-APY, IN-WB-KRISHAK-BANDHU, IN-WB-KANYASHREE, IN-WB-RUPASHREE | — | — | — | — |
| 5 | Semantic | Pradhan Mantri Kisan Samman Nidhi | en | IN-PM-KISAN | IN-PM-SYM, IN-PM-KISAN, IN-WB-KRISHAK-BANDHU, IN-WB-LAKSHMIR-BHANDAR, IN-PMSBY, IN-WB-SWASTHYA-SATHI, IN-WB-KANYASHREE, IN-PMJJBY, IN-APY, IN-WB-RUPASHREE | IN-PM-KISAN | — | — | — |
| 6 | Semantic | Lakshmir Bhandar | en | IN-WB-LAKSHMIR-BHANDAR | IN-WB-LAKSHMIR-BHANDAR, IN-WB-RUPASHREE, IN-PM-SYM, IN-WB-KANYASHREE, IN-PMSBY, IN-WB-SWASTHYA-SATHI, IN-WB-KRISHAK-BANDHU, IN-APY, IN-PMJJBY | — | — | — | — |
| 7 | Semantic | Kanyashree Prakalpa | en | IN-WB-KANYASHREE | IN-WB-KANYASHREE | — | — | — | — |
| 8 | Semantic | Rupashree Prakalpa | en | IN-WB-RUPASHREE | IN-WB-RUPASHREE, IN-WB-KANYASHREE | — | — | — | — |
| 9 | Semantic | Krishak Bandhu | en | IN-WB-KRISHAK-BANDHU | IN-WB-KRISHAK-BANDHU, IN-WB-SWASTHYA-SATHI | — | — | — | — |
| 10 | Semantic | Swasthya Sathi | en | IN-WB-SWASTHYA-SATHI | IN-WB-LAKSHMIR-BHANDAR, IN-WB-SWASTHYA-SATHI, IN-PM-SYM, IN-WB-KANYASHREE, IN-WB-RUPASHREE, IN-WB-KRISHAK-BANDHU | IN-WB-SWASTHYA-SATHI | — | — | — |
| 11 | Semantic | I need low cost insurance if an accident leaves me disabled | en | IN-PMSBY | IN-PMSBY, IN-WB-SWASTHYA-SATHI, IN-PMJJBY | — | — | — | — |
| 12 | Semantic | Life insurance to support my family if I die | en | IN-PMJJBY | IN-PMJJBY, IN-PMSBY, IN-WB-KRISHAK-BANDHU, IN-WB-SWASTHYA-SATHI, IN-APY | — | — | — | — |
| 13 | Semantic | I want to contribute now for a monthly pension after sixty | en | IN-APY, IN-PM-SYM | IN-APY, IN-PMJJBY, IN-PMSBY, IN-PM-SYM, IN-WB-KRISHAK-BANDHU, IN-WB-KANYASHREE, IN-WB-SWASTHYA-SATHI, IN-PM-KISAN, IN-WB-RUPASHREE, IN-WB-LAKSHMIR-BHANDAR | IN-PM-SYM | IN-PM-SYM | — | — |
| 14 | Semantic | I am a street vendor looking for a retirement pension | en | IN-PM-SYM, IN-APY | IN-APY, IN-PMJJBY, IN-PMSBY, IN-WB-KRISHAK-BANDHU, IN-PM-SYM, IN-WB-SWASTHYA-SATHI, IN-WB-RUPASHREE, IN-WB-KANYASHREE, IN-WB-LAKSHMIR-BHANDAR, IN-PM-KISAN | IN-PM-SYM | IN-PM-SYM | — | — |
| 15 | Semantic | Income support for a farmer who owns agricultural land | en | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN, IN-WB-SWASTHYA-SATHI, IN-WB-RUPASHREE, IN-WB-KANYASHREE, IN-APY, IN-PM-SYM | IN-PM-KISAN | — | — | — |
| 16 | Semantic | Monthly financial assistance for women in West Bengal | en | IN-WB-LAKSHMIR-BHANDAR | IN-WB-KANYASHREE, IN-WB-LAKSHMIR-BHANDAR, IN-WB-SWASTHYA-SATHI, IN-WB-RUPASHREE, IN-PMSBY, IN-PMJJBY, IN-APY, IN-PM-SYM, IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | IN-WB-LAKSHMIR-BHANDAR | — | — | — |
| 17 | Semantic | money for my daughter's education | en | IN-WB-KANYASHREE | IN-WB-KANYASHREE, IN-APY | — | — | — | — |
| 18 | Semantic | My daughter is getting married and we need financial assistance | en | IN-WB-RUPASHREE | IN-WB-KANYASHREE, IN-WB-RUPASHREE, IN-APY, IN-PM-KISAN, IN-PMSBY, IN-PMJJBY, IN-WB-SWASTHYA-SATHI | IN-WB-RUPASHREE | — | — | — |
| 19 | Semantic | Help for a farming family in Bengal after the farmer dies | en | IN-WB-KRISHAK-BANDHU | IN-WB-KRISHAK-BANDHU, IN-WB-SWASTHYA-SATHI, IN-WB-RUPASHREE, IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-PM-KISAN, IN-PM-SYM | — | — | — | — |
| 20 | Semantic | Cashless hospital treatment for my family in West Bengal | en | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI, IN-PMSBY, IN-PMJJBY, IN-WB-KANYASHREE, IN-WB-RUPASHREE, IN-WB-KRISHAK-BANDHU, IN-WB-LAKSHMIR-BHANDAR, IN-PM-SYM | — | — | — | — |
| 21 | Semantic | Insurance for accidental death through my bank account | en | IN-PMSBY | IN-PMSBY, IN-PMJJBY, IN-APY | — | — | — | — |
| 22 | Semantic | Bank account life cover with an annual premium | en | IN-PMJJBY | IN-PMJJBY, IN-PMSBY, IN-APY, IN-WB-SWASTHYA-SATHI, IN-WB-KANYASHREE, IN-PM-KISAN, IN-WB-LAKSHMIR-BHANDAR, IN-WB-KRISHAK-BANDHU, IN-WB-RUPASHREE | — | — | — | — |
| 23 | Semantic | I work as a domestic helper and earn little, can I save for retirement | en | IN-PM-SYM, IN-APY | IN-APY, IN-WB-KRISHAK-BANDHU, IN-PMSBY, IN-WB-KANYASHREE, IN-PM-SYM, IN-PMJJBY, IN-WB-SWASTHYA-SATHI | IN-PM-SYM | IN-PM-SYM | — | — |
| 24 | Semantic | A grant to help an unmarried girl stay in school in Bengal | en | IN-WB-KANYASHREE | IN-WB-KANYASHREE, IN-WB-RUPASHREE, IN-WB-SWASTHYA-SATHI, IN-PMSBY, IN-WB-LAKSHMIR-BHANDAR, IN-WB-KRISHAK-BANDHU, IN-PM-SYM, IN-PMJJBY, IN-PM-KISAN, IN-APY | — | — | — | — |
| 25 | Semantic | Support for a woman's first marriage in West Bengal | en | IN-WB-RUPASHREE | IN-WB-RUPASHREE, IN-WB-KANYASHREE, IN-WB-SWASTHYA-SATHI, IN-WB-LAKSHMIR-BHANDAR, IN-PM-KISAN, IN-WB-KRISHAK-BANDHU, IN-PMSBY, IN-PM-SYM, IN-PMJJBY, IN-APY | — | — | — | — |
| 26 | Semantic | West Bengal financial help for cultivating my farm | en | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | IN-WB-LAKSHMIR-BHANDAR, IN-WB-SWASTHYA-SATHI, IN-WB-RUPASHREE, IN-WB-KRISHAK-BANDHU, IN-PMJJBY, IN-WB-KANYASHREE, IN-PM-KISAN, IN-PMSBY, IN-PM-SYM, IN-APY | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | IN-PM-KISAN | — |
| 27 | Semantic | I need help paying hospital bills | en | IN-WB-SWASTHYA-SATHI | IN-PMJJBY, IN-PMSBY | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI | — |
| 28 | Semantic | Help with retirement | en | IN-APY, IN-PM-SYM | IN-APY, IN-PMJJBY, IN-WB-KANYASHREE, IN-WB-KRISHAK-BANDHU, IN-WB-SWASTHYA-SATHI, IN-PM-SYM, IN-PMSBY | IN-PM-SYM | IN-PM-SYM | IN-PM-SYM | — |
| 29 | Semantic | Help for farmers | en | IN-PM-KISAN, IN-WB-KRISHAK-BANDHU | IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | IN-PM-KISAN | — | — | — |
| 30 | Semantic | Support for girls | en | IN-WB-KANYASHREE, IN-WB-RUPASHREE | IN-WB-KANYASHREE | IN-WB-RUPASHREE | IN-WB-RUPASHREE | IN-WB-RUPASHREE | — |
| 31 | Semantic | Insurance | en | IN-PMSBY, IN-PMJJBY, IN-WB-SWASTHYA-SATHI | IN-PMSBY, IN-PMJJBY, IN-WB-SWASTHYA-SATHI | IN-PMJJBY, IN-WB-SWASTHYA-SATHI | — | — | — |
| 32 | Semantic | Help for women | en | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | ∅ | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | IN-WB-LAKSHMIR-BHANDAR, IN-WB-KANYASHREE, IN-WB-RUPASHREE | — |
| 33 | Semantic | School assistance | en | IN-WB-KANYASHREE | IN-WB-KANYASHREE, IN-WB-SWASTHYA-SATHI, IN-PMSBY | — | — | — | — |
| 34 | Semantic | Marriage support | en | IN-WB-RUPASHREE | IN-WB-RUPASHREE, IN-WB-KANYASHREE, IN-WB-SWASTHYA-SATHI, IN-WB-KRISHAK-BANDHU, IN-PM-KISAN | — | — | — | — |
| 35 | Semantic | Health cover | en | IN-WB-SWASTHYA-SATHI | IN-WB-SWASTHYA-SATHI, IN-PMSBY | — | — | — | — |
| 36 | Semantic | How do I renew my passport | en | ∅ | IN-PMJJBY, IN-APY | — | — | — | false positive |
| 37 | Semantic | Subsidy for installing solar panels on my rooftop | en | ∅ | ∅ | — | — | — | correct abstention |
| 38 | Semantic | Education loan for a master's degree abroad | en | ∅ | IN-WB-KANYASHREE, IN-PM-SYM, IN-PM-KISAN, IN-APY, IN-PMSBY, IN-PMJJBY, IN-WB-RUPASHREE | — | — | — | false positive |
| 39 | Semantic | How can I repair my laptop screen | en | ∅ | ∅ | — | — | — | correct abstention |
| 40 | Semantic | Unemployment allowance for a software engineer | en | ∅ | IN-PMSBY, IN-WB-KANYASHREE, IN-PM-KISAN, IN-WB-SWASTHYA-SATHI, IN-WB-KRISHAK-BANDHU, IN-APY, IN-PMJJBY, IN-PM-SYM, IN-WB-RUPASHREE | — | — | — | false positive |
