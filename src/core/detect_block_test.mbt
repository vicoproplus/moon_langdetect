///| V-33 / V-34 — compensated `sum(prob)` and naive `langprob` averaging,

///| plus `detect_block` (init -> rounds -> convergence `0.99999` ->

///| average) and the synthetic 0.1 threshold samples.
///

///| Float goldens are copied as big-endian bit patterns from

///| `docs/port/golden/float_add_python.json`:
///

///| * `float_sum_neumaier` / `float_sum_naive`: 307 groups in the golden

///|   order A-uniform (200), B-extreme (50), C-negative (50),

///|   E-stochastic (7). Inputs are replayed from the published recipe

///|   (`tools/gen_float_golden.py`, seed 0; `randbelow` drives the

///|   Fisher-Yates shuffle); the four embedded anchor values per scenario

///|   prove the replay matches the recorded Python inputs. No group is

///|   dropped: 307/307 Neumaier sums and 307/307 naive sums are compared,

///|   and the 238 groups where CPython's Neumaier `sum()` differs from a

///|   naive loop are asserted (V-33: 69/307 identical).

///| * `d_langprob`: 7 rounds x 55 languages = 385 naive

///|   `langprob[j] = langprob[j] + h[j] / 7.0` states (V-34). The `h`

///|   values are replayed from `random.Random(0)` with the published

///|   recipe; every post-round state is compared.

///| * `e_normalized`: 7 x 55 = 385 values proving `normalize_prob`

///|   divides by the Neumaier sum.
///

///| The threshold samples are synthetic and labeled as required by the

///| plan: `synthetic:基准 250 例中最小条目 0.1428…，无 ≤ 0.1（V-49）`.

///| They inject the three boundary probabilities directly because the

///| baseline corpus has no entry at or below 0.1; the strict `>` filter

///| itself belongs to Task 8's `_sort_probability` and is transferred

///|
/// there (documented below).
let uniform_55 : Double = 1.0 / 55.0

///|
let float_sum_neumaier : String = "403f56162d8364364039bd256889ff8d403c26d3d5f26e7d4039c0b557dbf1bc403cc16b6ad0a233403aa3dd8eb5c413403afd0c2e584136403a704162b4c113403a887fb3ea1857403ab1f58318536d40400a205efe19cd403cbd6d86351a82403a1104783c74b44039c9e52f4339c84040125cf00931f8403a73518e1685f2403aab67153ae7fa403f82a520e583be403a8e121fe92542403bf417003013e7403bbbbe0accaa5b403ec44695c35fca4038529e29863c5b403a8c185ef97663403d13119e892389403ed72124155f16403dc0d35b1a6e4740368f730de963cd403d7d7a5f6f48fa4039e2ae057dafd5403aaa847b724e29403cccde61070a114039d0999b68713c403c8e8006b4d9c04039811d67f57ae6403f4751d5683d3a40376a4d58c7fcb5403b20b2192f68c3403ef48ad104c55f4039931bb4b4ae744038faad7d64b208403b3d5383fff40b403e206f50d1b942403bede56d03ae57403ae85bd4f30d3d4039f57fce5d100d403ce3370a22d4ee403c6475a1ba5f4d" +
  "403aa4b72695b266403df86e9c3812e8403ae1767a065100403dc831ad946323403d83d67e352971403b8850c040820f40374176a040370740404688ba1baa89403c3487765551c8403dc0f937ee5311403c1ed0006acdef404059c615ac3d58403a72e5df9ec247403b2935758aef70403a28a2d1ddec4e403db8247332630c403a782221d24b6a4038efc8e793fc174038bbb4e4823fdd403edefba8ecf56c403d4fa772c512b9403d6f5598591c2c403c7f4d053a0661403d032f55b69c33403ba10cb4d61b0e403cc50c25818ed5403e054db5fcb4be40396c902bc84950403e3d5be9bcf14a40400a083326fd4e403e47397ba17c7b4038af8c3a379b53403b78e90098040140390347be51e6c2403befeb0b2b5da1403cc5cbef209c02403ba8928612c377403c6a64c1d4cb8840392ad6501538df403ba823a38ec342403b1437691dcb87403e3d9efcf7f93a403c7a4f280d1bd34039d0f25110efea403af6edfb37ccb64037d78c42150e1d403f623b801ed35d4037b71e75f7142d" +
  "403b230c0daa09b1403b25d013ae0b9a403b0491c5db2532403afaef7d555b6e4039095d8656dd09403bd917394429b2403b58e6688c7890403b42a3056841ae403c98975ecd53eb403a617130c399e4403a7f88615e9966403a7cd3ef7421e2403e95f72f60b3e6403cd8312c01837c403b8c5e25e2bbad403ccc3b4fcdab26403a6a10ce2200fd403d1b89c50da351403cce1aa89ce9cc4039c47265df9734403de1c043e3a023403bf2fc11eab1d1403d954ef748325b403d8e263f70030a403a685852c3da81403cb4ab42bb1ac64040a6998494d971403db38ca46a0005403b13f1b953a75e403e38317cbbfcc2403b9a437aa65579403e1a2d77445704403c3ab98c47aeb9403c817b4336fae5403c18ff112a5a72403bfb065989f9ea40392d423fdb03df4037cb89527cf08a403b49e12b3088ec403aaf81c43b774d403c3502cdcbb475403940e7f6514d8c403b49444df8aa97403d10e81201c850403c259df2013ae0403d9283893e2cb7403ab74d97488dd1403a4a2c3a5678b5" +
  "403b57593c7a486f403d18b5da1f1feb403c12a8680f7d3f403b96dc6e096ae440395d706989d8f2403c34ca6677691f403a3e0206813aa7403bc4151c58c205403d0d9e277d6b29403b8a3e90c56631403873095d4ef94a403ba55020785117403f283a9c126523403e22307f57e45140403ac7e99380de403de9590314f807403f4ba2423a2c104036a49ad348c519403adfe13229e18e403d3c82a64186e1403bd0711e720f734039b6277a4eae84403e50b75be88825403ec17a21c7ad0a403dea32ba81f37a403fec26b5f134f5403d53dc001028a1403da1ec4f9688e04037419a44f3f2fd4039d6374d590cb3403c11cd502d1b83403d9531cb072ed54035ee66ee75397e403c4b1fdf0715a74039d6c8b4c2c96d403bf61d13bf493d403c7d5001e84dea403d6bf8b6ee2fe2403c4b874457d3a0403a3e7217b236454039587e4f106866403e859e7f18af6b403d4e6a98131581403ca38856ab31e4403cff8c80395821403d6e9d79e6057c403b665babfe2f07403ec3cc43a0384e" +
  "403acdfef81ea8be403fa077694472c0403db93ec91d3d00403d3c173ffea7f9403cda6b90b68b6e403decfd76607829403f7885251a04d0403a0a3bad5428d87e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c" +
  "7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e84289312c0633c7e6d1b15cdc9d78e7e6ce3a86881ff687e6b234ff1c5648c7e6e32a9c8dd96447e6b29ac8b9047217e6d4aed7202d4bb7e699c8943048cfe7e6c2bedd103d4a47e6b6a5f0c0c83fb7e66b897a967c7487e6e535dd65fd62e7e6fad567b3c96567e6cd2218a833a287e6a7d7bc60940b97e6f395bcc424bc17e6dc278f21e3b8c7e6aaf4971ac70f47e6d93df77a99f487e6a081a4b9640777e6a6baaa513164b7e6bf6d55b1837b87e6b79ecd9dcb7a87e698f49f7a7cd487e6c99e9fa64b83f7e6c7bb775dc501a7e6bca90d066771c7e6bad14981de6707e6de114fc294bf87e6d40a65a1487f87e6d1593f7e146217e6d00be31841b5c7e6c97c353a9703b7e6b7e36c2140a167e6da6017013486e7e6afb3883a0233c7e6debd99d5b3fb57e6a43188b7610f67e69bd47ff11e35a" +
  "7e6d8b802f09ee767e6b10bf6e0f16357e6de5c98f84cc5f7e6a6f9e503ad8547e6b912dd5997faf7e6f2111b3e5f4207e6d088f8430f7937e6d6439c29376897e6d82bb2bc6c4297e6de09663e121887e6cc93c5e3d88247e6cd4ad51635add403b320c7abb2eca4039980b8b9d6259403496ec9791abfc403080c38ebecfb74030a146a36a909440380f58177547144034d670bb99aa91"

///|
let float_sum_naive : String = "403f56162d8364364039bd256889ff8c403c26d3d5f26e7d4039c0b557dbf1bb403cc16b6ad0a233403aa3dd8eb5c415403afd0c2e584139403a704162b4c112403a887fb3ea1857403ab1f58318536c40400a205efe19cd403cbd6d86351a83403a1104783c74b34039c9e52f4339c74040125cf00931f7403a73518e1685f0403aab67153ae7fd403f82a520e583be403a8e121fe9253f403bf417003013e7403bbbbe0accaa60403ec44695c35fc74038529e29863c5d403a8c185ef97661403d13119e89238b403ed72124155f15403dc0d35b1a6e4940368f730de963ce403d7d7a5f6f48f84039e2ae057dafd3403aaa847b724e2b403cccde61070a0f4039d0999b68713b403c8e8006b4d9bf4039811d67f57ae6403f4751d5683d3940376a4d58c7fcb3403b20b2192f68c4403ef48ad104c55d4039931bb4b4ae734038faad7d64b209403b3d5383fff40a403e206f50d1b941403bede56d03ae57403ae85bd4f30d3d4039f57fce5d100a403ce3370a22d4ed403c6475a1ba5f4a" +
  "403aa4b72695b265403df86e9c3812e9403ae1767a065100403dc831ad946320403d83d67e352971403b8850c040820f40374176a040370940404688ba1baa89403c3487765551c8403dc0f937ee5310403c1ed0006acdef404059c615ac3d59403a72e5df9ec249403b2935758aef70403a28a2d1ddec4d403db8247332630c403a782221d24b6b4038efc8e793fc174038bbb4e4823fde403edefba8ecf56c403d4fa772c512b8403d6f5598591c2c403c7f4d053a0661403d032f55b69c36403ba10cb4d61b0f403cc50c25818ed4403e054db5fcb4c040396c902bc84950403e3d5be9bcf14840400a083326fd4d403e47397ba17c7b4038af8c3a379b53403b78e90098040040390347be51e6c5403befeb0b2b5da3403cc5cbef209c03403ba8928612c376403c6a64c1d4cb8640392ad6501538dd403ba823a38ec33f403b1437691dcb85403e3d9efcf7f93a403c7a4f280d1bd44039d0f25110efeb403af6edfb37ccb74037d78c42150e1d403f623b801ed35b4037b71e75f7142c" +
  "403b230c0daa09af403b25d013ae0b99403b0491c5db2531403afaef7d555b6e4039095d8656dd0b403bd917394429b0403b58e6688c7890403b42a3056841ae403c98975ecd53ea403a617130c399e5403a7f88615e9965403a7cd3ef7421e0403e95f72f60b3e9403cd8312c01837b403b8c5e25e2bbae403ccc3b4fcdab25403a6a10ce2200fd403d1b89c50da34f403cce1aa89ce9cb4039c47265df9733403de1c043e3a020403bf2fc11eab1d0403d954ef748325d403d8e263f70030a403a685852c3da82403cb4ab42bb1ac54040a6998494d971403db38ca46a0003403b13f1b953a75e403e38317cbbfcc0403b9a437aa65579403e1a2d77445706403c3ab98c47aebc403c817b4336fae5403c18ff112a5a73403bfb065989f9ea40392d423fdb03de4037cb89527cf08a403b49e12b3088ea403aaf81c43b774c403c3502cdcbb476403940e7f6514d8a403b49444df8aa96403d10e81201c851403c259df2013ae0403d9283893e2cb6403ab74d97488dcf403a4a2c3a5678b5" +
  "403b57593c7a4871403d18b5da1f1fec403c12a8680f7d3f403b96dc6e096ae440395d706989d8f3403c34ca66776921403a3e0206813aa5403bc4151c58c205403d0d9e277d6b28403b8a3e90c5662f403873095d4ef94c403ba55020785118403f283a9c126521403e22307f57e45340403ac7e99380dd403de9590314f809403f4ba2423a2c114036a49ad348c519403adfe13229e18e403d3c82a64186e0403bd0711e720f744039b6277a4eae82403e50b75be88822403ec17a21c7ad0a403dea32ba81f37b403fec26b5f134f6403d53dc001028a0403da1ec4f9688e04037419a44f3f2fc4039d6374d590cb3403c11cd502d1b82403d9531cb072ed44035ee66ee753980403c4b1fdf0715a54039d6c8b4c2c96c403bf61d13bf4942403c7d5001e84dea403d6bf8b6ee2fe2403c4b874457d3a1403a3e7217b236454039587e4f106866403e859e7f18af6a403d4e6a9813157f403ca38856ab31e5403cff8c80395821403d6e9d79e6057e403b665babfe2f05403ec3cc43a0384c" +
  "403acdfef81ea8ba403fa077694472c0403db93ec91d3d00403d3c173ffea7fa403cda6b90b68b70403decfd76607828403f7885251a04ce403a0a3bad5428d97e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e" +
  "7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e84289312c0633e7e6d1b15cdc9d78f7e6ce3a86881ff6a7e6b234ff1c5648c7e6e32a9c8dd96457e6b29ac8b9047227e6d4aed7202d4bb7e699c8943048cfd7e6c2bedd103d4a17e6b6a5f0c0c83fc7e66b897a967c7457e6e535dd65fd62d7e6fad567b3c96597e6cd2218a833a277e6a7d7bc60940ba7e6f395bcc424bc47e6dc278f21e3b8a7e6aaf4971ac70f57e6d93df77a99f477e6a081a4b9640767e6a6baaa513164a7e6bf6d55b1837b97e6b79ecd9dcb7aa7e698f49f7a7cd487e6c99e9fa64b83e7e6c7bb775dc501c7e6bca90d06677197e6bad14981de6737e6de114fc294bfb7e6d40a65a1487f87e6d1593f7e146217e6d00be31841b5e7e6c97c353a9703a7e6b7e36c2140a187e6da6017013486d7e6afb3883a023397e6debd99d5b3fb37e6a43188b7610f87e69bd47ff11e35a" +
  "7e6d8b802f09ee777e6b10bf6e0f16357e6de5c98f84cc617e6a6f9e503ad8547e6b912dd5997fae7e6f2111b3e5f4227e6d088f8430f7957e6d6439c29376887e6d82bb2bc6c4297e6de09663e121897e6cc93c5e3d88237e6cd4ad51635add403b320c7abb2eca4039980b8b9d625d403496ec9791abfa403080c38ebecfb74030a146a36a909440380f58177547144034d670bb99aa90"

///|
let d_langprob : String = "3f9566c55b705e693f956388653b24e93f9556e5e9b20bdd3f9550d82193448a3f955a4b7b6c28b13f95564fff3bdc403f95648029c3c8f03f955281c1279cc53f9558ff06ebffcb3f955cfec6091f013f956927f63e24b53f955a0c530a92a23f9551b3e00f8c783f956373c811add53f955e4e315eff703f955087802f9a583f9569379ef884dc3f956bf3d8b8604a3f95657d702dcc8a3f9568eef2e07a7e3f9552c347af64b83f95627ac8ba19f93f9568cf0be7933e3f9560c33df16d7c3f9558d45307dc393f954aeb52630e4b3f9557684c5a1a4b3f955e06767cf93e3f956956eba7b2413f956b58bcde47ef3f955902fc1928ab3f95678d9c5b10253f9550e73c6ba37f3f95654baffbc9ce3f955bb245575a013f9547ac84d06da53f956219b23685563f9556156a33928e3f956609ac8fca403f95602b791a4e5b3f954730db8427833f9559a1d29d731e3f9567a3979dc4183f9550484527abb93f955353a113a6b83f9567bf1793239c3f954e4da8651b743f955c669da15722" +
  "3f95501581f021b63f956b61b0dd88283f956539f79ebf943f9557ec93ae30153f954a29224099973f955322423200e73f955a2b84b3e5343f9832992793889a3f981082ab25d7533f98146fa38fd2583f981432a8c97fbb3f9817b086710a913f981db5033df1803f9821a096d907ab3f981f7ecb2889093f98187a7e5c61ac3f981be4fc0fd7213f9822b6ccfa82743f981945a710c1473f980902a717de4e3f9821e746369ccb3f98121250564f5f3f980083edeb95063f98191a87efb5c33f982bcb3a925c563f9826f98e81a0bc3f9823ac2e04e5023f97ff05297e996c3f9827bea7e4a7b83f9832895d5b5cb93f982c3c6a5d61993f982145b638080c3f981572d3e775b93f9822de9bfcf52e3f981b29ebe663113f9820e3017d7fa33f982ea7038096453f980c3a38acd2c13f982ed76ac62ec73f98199bfaa7da143f982fb5257339ec3f981aad6bc792943f981422a2444ef03f9820b3f5679acc3f980fd9b13808773f9827a82bdd80f13f982e5f50b588ef3f98126c4af43bc6" +
  "3f98203c270d3c5e3f98139e09c4412d3f98101fbf5d90ae3f980e6fe5e222b23f98283d0a416e9d3f9816d82343dfbc3f980e6554c905103f98145f04a77c7c3f9818a9648a56c03f981660417ce7173f981e92f74f20fb3f97ff81e39998483f981a9523a561b23f9806d4c74384493f9ae0f9073b30f93f9ad387f6096c013f9abf0608e2746f3f9ad2950a1ec9663f9ae2a99194d6383f9ada9b188ae3a03f9ae4021f27e4523f9ac963791010263f9ad926f68b02f53f9adb7ead49f54d3f9ae12d30262f2d3f9ad0d0e842bc033f9abfc3ea2f7afb3f9aef8434bd42833f9abc53f0f4e61d3f9aaa381888d5233f9ae5fca82905f03f9adb9d49f328b13f9ad482132a287f3f9ad473b5d86c543f9ac5e6a44a09453f9af3ba193ed5db3f9adc4884b901863f9ae5118d78ad1a3f9acdf787b3b6673f9ac813698f89913f9ad4086ed426023f9adc48b934438a3f9ad6e60143f6323f9ade4c749fb2fa3f9ac7fb4ffc10093f9ad935ad7a612f3f9ac6483f2bf69c3f9afd9c133b3c31" +
  "3f9acb0960f6d4953f9aca74d58fbe433f9ae4fe83d881143f9ad823734e80b13f9af2f260f21fc43f9add9c52c65d973f9ad4819f59efc93f9aed532cfecb7a3f9abeaf4f201de43f9ad25737f309d63f9ad6fdb46dadcd3f9addf3857aba563f9ac92035c704123f9acda37f10bb1b3f9acdd4363e74ff3f9ac81a1f1404013f9ad0ee7508d4413f9ad6d1757276163f9abdb6b31288463f9ad685d10430053f9abb6357c18a773f9d973dc5abb5803f9d9bcb5713ebc43f9d7150757dc1cf3f9d90783d9808823f9d8c0588785def3f9d9f454aed15a63f9d997b48ebad593f9d73fe4d4d3b573f9d8c9085ac397d3f9d8d618a45bba43f9dadc38ee6b7b53f9d86e66caf05cd3f9d7370884d120d3f9da5dc993c2dfe3f9d88aea59151573f9d6ad88fd533643f9da623a56cbf7a3f9d9f4ea7c426aa3f9d8beeb9e999653f9d8cdd771737743f9d872ae6c3a5223f9d9cad72ef384d3f9d8c60ec87b83b3f9d9a7c315b1ac03f9d7fd38b3d7e7e3f9d88d6e2bc2a163f9d8b1b4324d1a8" +
  "3f9da5f620cf5e6b3f9d95119967c2783f9d96b6196b95393f9d7ff093a4f79d3f9d9c62d79faa763f9d7ed683a70db63f9dbf4d459bb2bc3f9d75ae97a57ff13f9d84072798ed013f9d979874c71f373f9d86efed1a47c23f9daf98f31feb0d3f9d98c07783a0b63f9d926c89ca4ac53f9db282bb30a3813f9d88adbd9d0a6d3f9d8dc182bb08b63f9d8b922388d1ec3f9d98545889fd223f9d905141307ef03f9d974cffa3008a3f9d95258e4404803f9d7809394bf01c3f9d9f409e4f45af3f9d976b9b28277a3f9d69bba257cd673f9d9a966dfd016a3f9d893cb8046c293fa027975c2513933fa02f0c7e7637e03fa0130630ba422f3fa020ae047c861a3fa027e39f26e3dc3fa0242050ee36013fa03097c42ad1d93fa01856242059393fa01c8f5bb335ca3fa01d5d1a82d81b3fa0377c653bb3f33fa028416ea618aa3fa01368bac75be03fa039b32bd12f343fa01aa9e84918053fa019dbfe68dd193fa02ef1c04e920c3fa0259f9ffdae7a3fa01f8e91f0d9093fa0235c72ad6c80" +
  "3fa026dde6a650dc3fa032ea037e1d6b3fa01d226184ee453fa02b713aa4fc5a3fa0208ba9f653663fa01f5d682c60073fa02a5345530b283fa02ca3fcd726d63fa01f54344da1cc3fa02090566593943fa0212b0233b1733fa02d184344c60a3fa02596ad4065c73fa045ab66ed12a13fa02053071da43c3fa0173f4b636a793fa02e459141e0ad3fa0250c2028ccf53fa03884507d913f3fa02e29482069973fa02e8fc531c1963fa039b03ebc352d3fa01fc2923335b13fa02565ae396a843fa01e1fbca735193fa02b9aec12d2443fa01cc5a4ec4cf53fa022eccbd649113fa025435628fef73fa01f40081c33e83fa03186cc4be5193fa0267d993c6d7f3fa014eebab37f983fa0228316ef635f3fa01c2231324da63fa18e6c863a63df3fa188eab9e56a663fa16edcfd9f13da3fa17f658a5e73fa3fa181d46f231dbf3fa1818648873bc13fa1898729f4e27d3fa16dafd38be9313fa1745e93296b8d3fa17b9ab56677ce3fa18d4271dfb82b3fa184406370cf293fa16e01dbf8f8cc" +
  "3fa195e98105dcb73fa170f8c0314c6d3fa17f5200f7a5cc3fa18c4441b872203fa189d0979485663fa186487c3edef23fa17e3e1b7c52cd3fa18448c4319cac3fa19475e2bda69b3fa1799157bae7d63fa1858ac47f342c3fa182c00df2b88e3fa1848f12893ec63fa18ffe28bf720a3fa18cd2a36e529c3fa17acedee8e1223fa1874240b1ada83fa18193d5dcc3763fa182c635a0d4563fa17b9ee889c3bb3fa1a828436dca273fa175ea8c4e48d93fa16bd74c0a76e13fa18a17a69d0d803fa183365572f7b43fa1955cc6a2e2003fa18bc1d70eb55b3fa18df5cc248f743fa19adad81a19863fa17c20c4d172833fa180bda484e2003fa18514464f7cb23fa184effdeb48c93fa17fc508fc8ae53fa17f7238075ad03fa1806c44f4f2b43fa174e480c29ae13fa19624b9618bec3fa188150479b1683fa17a49abd2eacc3fa17f6a415256123fa17d4160057ae13fa2e518e37251513fa2e4d0ae84a4913fa2c730b9577cfa3fa2d4a1b8dce3e13fa2e806d8b384a43fa2da038a29f3de" +
  "3fa2e0b714e069053fa2c5d729a471583fa2cfe5094668183fa2da4832d9ae943fa2e48a3bc519e83fa2eb36085bbade3fa2d4dc2d658a6e3fa2ed233c88425c3fa2cd04d48d8b033fa2e07f9ba4b9353fa2f125a9f27a533fa2e789af36c9373fa2ebe6b55f23083fa2d8ba2fc3f5a73fa2e210682308493fa2f23e831b0ecf3fa2da8fad3c46513fa2ddc56138d8f43fa2e29d5a51fddc3fa2dd1a20c17ead3fa2eacf5eeb47cb3fa2f34b0f6adbac3fa2e016a038f6e23fa2eb06439907f53fa2d6b0389370a73fa2d9ffc605d18e3fa2d4e0a35cb5953fa30b4986ece4253fa2da22a22e74f43fa2cb3405b5c6963fa2ebfc6073756c3fa2e6c55092d7843fa2eb0d3c9215723fa2e1c9f1e879343fa2f2ad351f712d3fa2f00a270206583fa2d4ca1b8607aa3fa2d5f2c7dc886f3fa2d9cfe9a387743fa2e92fd96b12263fa2da681ad5a7313fa2d6e6da9b914f3fa2d7a800c2f4f03fa2d59fcd6e035e3fa2fcba0f33a84e3fa2e5fc18f16cc23fa2df9b689136293fa2dd4502b6d1f2" +
  "3fa2dc7298977228"

///|
let e_normalized : String = "3f90556bccf165c13f95dd9abb8b811f3f8d0c46863967243f9312e7879181913f906728602a36e13fa09755b12d01a83f9d6ba534279a363f97e1b46314f7ef3f8577a5e5efa81a3f98c57fb1dc79583f9e3a413142aa873f94b3ad77e5a9983f9271a6e9e2a1b53f85cf4a4b734d163f90828b528c1dea3f810eebcfecb5be3f98ada57ef9a32e3f824e751f36b8623f99557657eac5a83f9b61fb4df1edbc3f94876ac0722b5b3f9444a302a4fa723f87d145e897c9a43f8809598466f57b3f875a2a5fe297733f9fd915ccf575993fa10a8c96b9966b3f9522f87a8fda353f924462718a5bcc3fa1a10e6ae8931c3f954be98b7adba43fa14f0b5b0cbfe73f8312742776b8163f8dbc9b57d8d9213f8d7fce80977c6e3f9cf99fa483277d3f85d7aa399ea1713f892930c27700163f82ecbb99df83f23f952416573db1393f95e7934e5b87563f8690e853f769013f7e22621756764f3f885421842935ac3f86a9d77b7d40bc3f84ce991e1cf5923f783c283200fa843f7df567f8da9fa2" +
  "3f93ebd9e9870a543f9c16714bdbae6b3f9cf2e0751d58b03f913bbfc5aaa2983f892b506391d5193f9173da862938e63f8cd037b10b2ee73f7b6aabc34447c63f885f2c8570b8a13f9356d5f685f4a73f89623984afd2dd3f9e1d6d521ff6c73f940f6535a4fd2c3f8b95cfe98e104f3f904d6ca100ba953f9193297e4b02d83f9375e42c5785ca3f825b26fa41f8293f85b3f1e3952a483f93ab6968a8c68a3f9790ba64d9078c3f92cc370318a0103f91c77fcf30f26a3f90428bfbcbe90c3f950924bcf2ae8a3f8e16044f784d973f9c0a506134cf2c3f85fe156b3e55783f90e06cc8904eec3fa1df67ceef900e3f879178ae72382d3f981ccec3aa98cd3f896af17ab322343f88a946e99c074c3f829dcc74bfbc353f9cd3ad3a668d6c3f9f30625ce0a3fd3f9ae99480e0269d3f96b54fc2fbad963f93c11c528b68653f7a64625e84246f3f9421f1d09f5d513f89c939b03959593f98054a0afb37ab3f92234c106efe3e3f807e89fe0466ba3f8fd0293d0ac2463f8177c0a22948d4" +
  "3fa14db36d90acd23f9a4869b84e32093f916845d6b35e8c3fa08d3a82311e3b3f9dccada1d617c43f872dc3393a9e1b3f8648e50d713ed93f8e69941cf02f5b3f953443ab2304613f983f3885d993543f8a130dca46e1c83f93b21fdc8123b33f959bad29f7074c3f928ca980b5cb6b3f7d225a860dac623f81f2e83877bd6a3f99f72b448470763f970c45b9bb9ea43f9598f12a0580293f98a077229690563f8911d84f14fc033f8f8b8d5e48aa0d3fa1c0401f7f5f9a3f786a04db4a4e073f9978d65227df3a3f892be54d2535aa3f77361f64c647703f773cac072e098e3f8ed8fbdef0b1dd3f90c0039ce95ea03f9297992e3468ea3f9921e679e88e773f9d2ffe8501f78b3f99067a1ec740373f93b82f63a54d663f9876cb471bdf2a3f9c82cc2441b4513f7e363e8b61d05a3f9025ea0d3a1d9c3f96c8eb3bc8ab933f992a492b146cd13f8ad90841965cf23f7dee58e2c087ff3f962ac6497b90823f9d65e63bfebeaa3f8c8ff5a35710a53f77a7241311856f3f84bc512b16893e" +
  "3f8182df768cca133f8fb45bbe384eb23f97e9cefb9f5a763f8853568039cdc73f9b3356928d33d83f8e41c0615c4b523f9ebdea89ca8d4b3f9dd1411906ebd93f87890eed9908133f9c70864ebdc4a13f887d773d2dc0383f9a4c25f21391703f8da0ba8591114f3f8dfcea3abb463f3f953b7a1115c6a93f87f04333ed1c283f9c504424b3e5a33f92ff809efbd7fd3f937da6b7f5c8af3f9bf8d765bad1233f8ea65e9e1ce0a43f8b13e706fbc8c03f8e24b43965fbc03f81a898b09ed1023f95169e8b0da86f3f82db81d001fa943f8ccca9e469afdd3f852dbf88355d103fa5597b50cd064f3f8b992f2d9b43823fa1ba4c25baff093f82543e9ff56ac53f9d7ecc56bae0253f993a00a79b21493f88e234e94b1a8a3f85e50fbf7f69443f74578eaf8be9723f9770c2c93a36203f8c86839a03dcdc3f83c89cb0196dc73f9a0d78ea32a0043f8fcd9907fd810a3f8a2557ba4907ff3f98149aeccab20f3f9cda0a6d5c50933f980d325d72edb03f91596f01459f1c3f9b9ad8bc7293ee" +
  "3f9069982512e4643f87443b4f0dcdf13f878dd1d4148f1f3f8ea12cb0ce6b523f9d2d48416757273f9fc4de530809903f8566b7a0fc6d153f9498c1a213595a3f930bbf67bc50a23f817b281eb523d43f9dc29a47ab600d3f8261005828d7ef3f89a0e74fa664c93f99f6bb9a0012af3f912f638d98fe683f952eb447946ce53f9d6e6e3610f3f43f96a1e3fd2b674f3f9a7ded8b11c9283f8742827bbe48083f96f115af8bb2e93f96299e34b5760a3f8312927ea1d2a03f82b2efed0556ee3f94f2054939bc2c3f9bf68878f516213f8d30637ce30c933f8a79e35be81ebd3fa08602bb7174803f9213b3433385473f8dccf8db68d0ce3f88f01859cb4cf23f9251364d0e8e8e3f94032277b950173f898164adfbd4ff3fa0cca50f47f7693f876e3202275c793f9033e5dcd8d79f3f83b28f9af0c3af3f8b80f6c9d9d5f13f8e0e840843cf513f9314784f99e5683f9a4c5f06796dc63fa09c0a381abdf53fa61c0646c9563e3f9a15b72343e0033f7cfcc7f9cbfa443f8a5f2e5d7f341d" +
  "3f8f8b56437fa8df3fa4fbff65f5a0c43f8654d21793bde63f97cb90da09a03c3f839ab8961e91f53f7c910945a2d26a3f8b6f673182b4f63f93c4668f12d7fe3f9698998235a6843fa085ee3043dce73f8ac7720f2c2bd93f90fc41edcc9f253f84ee4bd4dd05193f86b5d09e4a8aea3f907f97583b24c13f999900283471e93f8292a01e88e4463f932b10e69db90d3f90f0990c9c48ba3f85eead2cdc37e63f9132317d080c823f8d4d202418d7913f7ee592b51aa41b3f92e7ed6735e7043f9f94d4dac9afc43f8aa4d238482e893f9b0c8607bcc1473f952a569036828f3f9df7d8a158869e3f912c55383587a83f87538db4b8e4113f8da7a29e2a59603f818152a010e5963f919cf9556b52483f97ed921a73cdfa3f9d37e791e6eaec3f91dd0fcef29ec93f99d5f5cc4869983f8b0801ff4b0def3f95eaa61fd7ac143f884deb64de97823f96135fc3e3609e3f96a368f272d4d83f9bdd852efa89be3f9e4456391420453f80bcdb1f47685c3f947e52808d49f23f94f6c2df0eda32" +
  "3f8723c08eac9c4a3f93bc6d995d0ac43f886657714178b43f7833b5a43f69123f8790d759ea36bb3fa389dd6b1f115c3f864f6dc597270f3f91d13d6b34b4223f955bd43e89456d3f917b7191b23fc43f8854c7cb5b959c3f980f5419b1b1073f863185986750ca3f895f8b9dd9601e3f954d4b7b2b72a53f90a043ccda2dcf3f8e4c613f85b5543f901a2cf585b8b63f941e5d52c90f6c3f821a29df2824933f8aca3ad15679583f8f30b99eb48bf53f847da298e8081d3f8db6a98bd8a2043f89539c8909c8ec3f90ac8579ed0a733f9ef3c76b77d0e53f8ba1ed912b0c233f96ecc3b067ce243f74cfa65559dc513f9cd0b7ff5d58523f8535acf14dbcbc3f9c282c016160153f9d6d7c3fe2b4573f975966c0f1fdef3f98cb73cff701f13f977383cd9d465a3f803c07fecbb97c3fa25708db4d63853f8ae35bd6dc48ff3fa257917a3bee983f718c3193d860bd3f98b53382cc50fb3fa019851b5d229a3f9524fac95179ac3f86192ba6e8e82a3f7d9a0e0a36ee8d3f89810643f75b20" +
  "3f8d368382563d8b3f92eddec5d0d2a13f96537ed81fcfba3f89e815192199a33f9dee6796e81ccc3f975f04355417323f94cbeff29aa7f53f966d6ded6ca46b3f8c30fb75625fae3f87ca0ccfc20dee3f96a5abf50031403f89ac298691d7343fa08977ebf430bf3f95d1bd9cf775053f94ee537de1e7133fa06101daca7c7f3f90debd1767686a3f8e2e0c48c9f2f83f9a916c1a11884e3f71078b13984cba3f86e7d92bf527da3f9351f1ae6a7ea53f95572216e70fce3f99f67668e013353f8841719bdcb7623f90ea8a3386f21a3f819ae157c410d03f7596fc84d090b83fa2031d71788c073f955b1a894cb4883f98362ad8a16f613f8d198486c5950e3f745ca756d0d8fd3f9506dc5faf9af63f74b044c84aec193f948f87f3cad8ec3f9a237159e5302c3f88f1d5922a84193f8a01be97f8df893f90da028497a8bb3fa11f2c21dda6653f91ce4f0f8eb7da3f968fcfe3c064113f983bf92f3b91123f8d2e4dee9d0a393f87bdb7cced32c73f910e6b26a77ffc3f9ca5c48247c8cf" +
  "3f7f1abde1ffd64b"

///|
let float_anchor_a : Array[UInt64] = [
  0x3FD0284AF2D1AA0DUL, 0x3FD07D77C730C7FEUL, 0x3FE73191CB0223C4UL,
]

///|
let float_anchor_b : Array[UInt64] = [
  0x0000000000000001UL, 0x7E37E43C8800759CUL, 0x7E37E43C8800759CUL, 0x01AAFA92CFDF7ACAUL,
  0x7E37E43C8800759CUL, 0x01AE1BA49AC4028BUL,
]

///|
let float_anchor_c : Array[UInt64] = [
  0x7E0931A0EE7A00D6UL, 0x7E11A26330117323UL, 0x7E17DF3B5EE48E9CUL,
]

///|
let float_anchor_e : Array[UInt64] = [
  0x3FDBC33D981313E3UL, 0x3FE2952D56F98A24UL, 0x3FD8AFCA03755222UL,
]

///|
let fixed_const_bits : Array[UInt64] = [
  0x0000000000000001UL, 0x7E37E43C8800759CUL, 0x01A56E1FC2F8F359UL, 0x3FB999999999999AUL,
  0x3F929E4129E4129EUL, 0x3F50624DD2F1A9FCUL,
]

///|
/// Explicit left-to-right sum (the V-33 comparison baseline).
fn naive_sum(values : Array[Double]) -> Double {
  let mut acc = 0.0
  for value in values {
    acc = acc + value
  }
  acc
}

///| A-uniform group: 55 draws in `[1/55, 1)` then Fisher-Yates with

///|
/// `_randbelow`, matching `tools/gen_float_golden.py::gen_a`.
fn gen_a_group(rng : @core.Mt19937) -> Array[Double] {
  let xs : Array[Double] = []
  for _index in 0..<55 {
    xs.push(uniform_55 + rng.random() * (1.0 - uniform_55))
  }
  let mut i = 54
  while i >= 1 {
    let j = rng.randbelow(i + 1)
    let tmp = xs[i]
    xs[i] = xs[j]
    xs[j] = tmp
    i -= 1
  }
  xs
}

///| B-extreme group: 1.0e300 / 1.0e-300 alternation plus the five fixed

///|
/// overrides of `gen_b`.
fn gen_b_group(rng : @core.Mt19937) -> Array[Double] {
  let xs : Array[Double] = []
  for index in 0..<55 {
    let u = rng.random()
    if index % 2 == 0 {
      xs.push(1.0e300)
    } else {
      xs.push(1.0e-300 * (1.0 + u))
    }
  }
  xs[0] = 5.0e-324
  xs[1] = 1.0e300
  xs[11] = -1.0e300
  xs[53] = 1.0e-300
  xs[54] = 1.0e300
  xs
}

///| C-negative group: positive and negative 1.0e300-scale values, as in

///|
/// `gen_c`.
fn gen_c_group(rng : @core.Mt19937) -> Array[Double] {
  let xs : Array[Double] = []
  for _index in 0..<55 {
    let u = rng.random()
    let p = uniform_55 + u * (1.0 - uniform_55)
    xs.push(p * (1.0e300 - 1.0e300 * u))
  }
  xs
}

///|
/// E-stochastic: 7 groups of 55 positive values, `gen_e` call order.
fn gen_e_groups() -> Array[Array[Double]] {
  let rng = @core.Mt19937::new(Some(0L))
  let groups : Array[Array[Double]] = []
  for _group in 0..<7 {
    let alpha = 0.6 + 0.25 * (rng.random() - 0.5)
    let probs : Array[Double] = []
    for _index in 0..<55 {
      let w = 0.3 + rng.random() * 0.7
      let base = alpha * w + (1.0 - alpha) * uniform_55
      let noise = 0.05 * (rng.random() - 0.5)
      probs.push((base + noise) * (0.5 + rng.random()))
    }
    groups.push(probs)
  }
  groups
}

///| V-33: 307 groups, Neumaier and naive sums both bit-exact, and the

///|
/// 238 differing groups recorded.
test "float_sum_307_groups" {
  let neu_expected = hex_values(float_sum_neumaier)
  let naive_expected = hex_values(float_sum_naive)
  assert_eq(neu_expected.length(), 307)
  assert_eq(naive_expected.length(), 307)
  let rng_a = @core.Mt19937::new(Some(0L))
  let rng_b = @core.Mt19937::new(Some(0L))
  let rng_c = @core.Mt19937::new(Some(0L))
  let mut group = 0
  let mut neu_bad = 0
  let mut naive_bad = 0
  let mut differing = 0
  for _index in 0..<200 {
    let xs = gen_a_group(rng_a)
    if group == 0 {
      assert_eq(xs[0].reinterpret_as_uint64(), float_anchor_a[0])
      assert_eq(xs[1].reinterpret_as_uint64(), float_anchor_a[1])
      assert_eq(xs[2].reinterpret_as_uint64(), float_anchor_a[2])
    }
    let neu = @core.neumaier_sum(xs).reinterpret_as_uint64()
    let naive = naive_sum(xs).reinterpret_as_uint64()
    if neu != neu_expected[group] {
      neu_bad += 1
    }
    if naive != naive_expected[group] {
      naive_bad += 1
    }
    if neu != naive {
      differing += 1
    }
    group += 1
  }
  for _index in 0..<50 {
    let xs = gen_b_group(rng_b)
    if group == 200 {
      let mut anchor = 0
      while anchor < 6 {
        assert_eq(xs[anchor].reinterpret_as_uint64(), float_anchor_b[anchor])
        anchor += 1
      }
    }
    let neu = @core.neumaier_sum(xs).reinterpret_as_uint64()
    let naive = naive_sum(xs).reinterpret_as_uint64()
    if neu != neu_expected[group] {
      neu_bad += 1
    }
    if naive != naive_expected[group] {
      naive_bad += 1
    }
    if neu != naive {
      differing += 1
    }
    group += 1
  }
  for _index in 0..<50 {
    let xs = gen_c_group(rng_c)
    if group == 250 {
      assert_eq(xs[0].reinterpret_as_uint64(), float_anchor_c[0])
      assert_eq(xs[1].reinterpret_as_uint64(), float_anchor_c[1])
      assert_eq(xs[2].reinterpret_as_uint64(), float_anchor_c[2])
    }
    let neu = @core.neumaier_sum(xs).reinterpret_as_uint64()
    let naive = naive_sum(xs).reinterpret_as_uint64()
    if neu != neu_expected[group] {
      neu_bad += 1
    }
    if naive != naive_expected[group] {
      naive_bad += 1
    }
    if neu != naive {
      differing += 1
    }
    group += 1
  }
  let e_groups = gen_e_groups()
  for e_index in 0..<7 {
    let xs = e_groups[e_index]
    if group == 300 {
      assert_eq(xs[0].reinterpret_as_uint64(), float_anchor_e[0])
      assert_eq(xs[1].reinterpret_as_uint64(), float_anchor_e[1])
      assert_eq(xs[2].reinterpret_as_uint64(), float_anchor_e[2])
    }
    let neu = @core.neumaier_sum(xs).reinterpret_as_uint64()
    let naive = naive_sum(xs).reinterpret_as_uint64()
    if neu != neu_expected[group] {
      neu_bad += 1
    }
    if naive != naive_expected[group] {
      naive_bad += 1
    }
    if neu != naive {
      differing += 1
    }
    group += 1
  }
  assert_eq(group, 307)
  assert_eq(neu_bad, 0)
  assert_eq(naive_bad, 0)
  // V-33: CPython's `sum()` is Neumaier; only 69/307 groups equal the
  // naive loop, so 238 differ.
  assert_eq(differing, 238)
}

///|
/// V-34: 385 post-round `langprob` states of the naive average.
test "langprob_naive_385_states" {
  let expected = hex_values(d_langprob)
  assert_eq(expected.length(), 385)
  let rng = @core.Mt19937::new(Some(0L))
  let langprob = Array::make(55, uniform_55)
  let mut bad = 0
  for round in 0..<7 {
    let h : Array[Double] = []
    for _index in 0..<55 {
      h.push(uniform_55 + 1.0e-3 * rng.random())
    }
    let mut j = 0
    while j < 55 {
      langprob[j] = langprob[j] + h[j] / 7.0
      if langprob[j].reinterpret_as_uint64() != expected[round * 55 + j] {
        bad += 1
      }
      j += 1
    }
  }
  assert_eq(bad, 0)
}

///| `normalize_prob` divides by the Neumaier sum; 385 E-stochastic

///|
/// quotients are compared bit-for-bit.
test "normalize_prob_matches_385" {
  let expected = hex_values(e_normalized)
  assert_eq(expected.length(), 385)
  let groups = gen_e_groups()
  let mut bad = 0
  let mut maxp_bad = 0
  for group in 0..<7 {
    let probs = groups[group].copy()
    let maxp = @core.normalize_prob(probs)
    let mut golden_max = 0.0
    let mut j = 0
    while j < 55 {
      let bits = expected[group * 55 + j]
      if probs[j].reinterpret_as_uint64() != bits {
        bad += 1
      }
      let golden_value = UInt64::reinterpret_as_double(bits)
      if golden_max < golden_value {
        golden_max = golden_value
      }
      j += 1
    }
    if maxp.reinterpret_as_uint64() != golden_max.reinterpret_as_uint64() {
      maxp_bad += 1
    }
  }
  assert_eq(bad, 0)
  assert_eq(maxp_bad, 0)
}

///| V-51 / C1 NaN path: a NaN vector propagates through every quotient,

///|
/// `maxp` stays 0.0, and the loop still visits all entries (no reject).
test "normalize_prob_propagates_nan" {
  let nan = 0.0 / 0.0
  let prob : Array[Double] = [nan, 1.0, 2.0]
  let maxp = @core.normalize_prob(prob)
  assert_eq(maxp, 0.0)
  assert_true(prob[0].is_nan())
  assert_true(prob[1].is_nan())
  assert_true(prob[2].is_nan())
}

///| Bit patterns of the literals used by the recipes: 5.0e-324 is the

///| smallest subnormal, 1.0e300 / 1.0e-300 / 0.1 / 1/55 / 1.0e-3 are the

///|
/// nearest doubles (same as CPython).
test "recipe_constants_bit_exact" {
  let values : Array[Double] = [
    5.0e-324,
    1.0e300,
    1.0e-300,
    0.1,
    1.0 / 55.0,
    1.0e-3,
  ]
  let mut index = 0
  while index < values.length() {
    assert_eq(values[index].reinterpret_as_uint64(), fixed_const_bits[index])
    index += 1
  }
}

// ---------------------------------------------------------------------
// detect_block
// ---------------------------------------------------------------------

///|
/// Two-language synthetic vocabulary (vectors are [lang0, lang1]).
fn synthetic_map() -> Map[String, Array[Double]] {
  let map : Map[String, Array[Double]] = Map([])
  map.set("a", [0.6, 0.4])
  map.set("b", [0.4, 0.6])
  map.set("ab", [0.55, 0.45])
  map.set("abc", [0.5, 0.5])
  map
}

///| Raw extraction of the synthetic text: 23 grams, only 9 of which are

///|
/// vocabulary entries (R19 raw -> filtered).
test "detect_block_filters_raw_ngrams" {
  let raw = @core.extract_ngrams("a ab abc b")
  assert_eq(raw.length(), 23)
  let map = synthetic_map()
  // The same membership filter `detect_block` applies: raw order and
  // duplicates preserved, grams absent from the vocabulary dropped.
  let filtered : Array[String] = []
  for word in raw {
    if map.contains(word) {
      filtered.push(word)
    }
  }
  // The map holds 4 of the 23 raw grams; 9 occurrences survive.
  assert_eq(filtered.length(), 9)
  let expected : Array[String] = [
    "a", "a", "b", "ab", "a", "b", "ab", "abc", "b",
  ]
  let mut index = 0
  while index < expected.length() {
    assert_eq(filtered[index], expected[index])
    index += 1
  }
  let probs = @core.detect_block(
    "a ab abc b",
    map,
    alpha=0.5,
    seed=Some(42L),
    prior_map=None,
    n_trial=7,
  )
  assert_eq(probs.length(), 2)
}

///|
/// No vocabulary hit -> upstream code 5 with the four-field payload.
test "detect_block_no_features_raises_code_5" {
  let map = synthetic_map()
  let mut raised = false
  let mut seen_code = -1
  let mut seen_message = ""
  let mut seen_len = -1
  let mut seen_prefix = ""
  try {
    let _ = @core.detect_block(
      "!!!",
      map,
      alpha=0.5,
      seed=Some(42L),
      prior_map=None,
      n_trial=7,
    )
  } catch {
    CantDetect(code~, message~, input_len~, input_prefix~) => {
      raised = true
      seen_code = code
      seen_message = message
      seen_len = input_len
      seen_prefix = input_prefix
    }
  }
  assert_true(raised)
  assert_eq(seen_code, @core.ERROR_CANT_DETECT)
  assert_eq(seen_message, "No features in text.")
  assert_eq(seen_len, 3)
  assert_eq(seen_prefix, "!!!")
}

///| Exact upstream replay of the synthetic map: seed 42, no prior, 7

///| rounds. Bits generated with CPython 3.12.10 `random.Random(42)` and

///|
/// the upstream `_detect_block` body (scratch script `gen_detect_block_golden.py`).
test "detect_block_synthetic_seed42" {
  let map = synthetic_map()
  let probs = @core.detect_block(
    "a ab abc b",
    map,
    alpha=0.5,
    seed=Some(42L),
    prior_map=None,
    n_trial=7,
  )
  assert_eq(probs.length(), 2)
  assert_eq(probs[0].reinterpret_as_uint64(), 0x3FEFFFF204D03D5AUL)
  assert_eq(probs[1].reinterpret_as_uint64(), 0x3EDBF65F854DB7AAUL)
}

///| Prior vector path: `_init_probability` copies the normalized prior

///|
/// every round (seed 7, prior [0.7, 0.3]).
test "detect_block_synthetic_prior" {
  let map = synthetic_map()
  let prior : Array[Double] = [0.7, 0.3]
  let probs = @core.detect_block(
    "a ab abc b",
    map,
    alpha=0.5,
    seed=Some(7L),
    prior_map=Some(prior),
    n_trial=7,
  )
  assert_eq(probs[0].reinterpret_as_uint64(), 0x3FEFFFF37E1DB0ADUL)
  assert_eq(probs[1].reinterpret_as_uint64(), 0x3ED903C49EA660ADUL)
}

///|
/// Same seed, five independent calls: bit-identical `langprob`.
test "detect_block_same_seed_5x" {
  let map = synthetic_map()
  let baseline = @core.detect_block(
    "a ab abc b",
    map,
    alpha=0.5,
    seed=Some(42L),
    prior_map=None,
    n_trial=7,
  )
  let mut run = 0
  while run < 4 {
    let again = @core.detect_block(
      "a ab abc b",
      map,
      alpha=0.5,
      seed=Some(42L),
      prior_map=None,
      n_trial=7,
    )
    assert_eq(again.length(), baseline.length())
    let mut j = 0
    while j < baseline.length() {
      assert_eq(
        again[j].reinterpret_as_uint64(),
        baseline[j].reinterpret_as_uint64(),
      )
      j += 1
    }
    run += 1
  }
}

///| Unseeded `detect_block` never raises; ten runs are allowed to differ

///|
/// because the generator is reseeded from time xor counter each call.
test "detect_block_unseeded_10x_no_exception" {
  let map = synthetic_map()
  let mut run = 0
  while run < 10 {
    let probs = @core.detect_block(
      "a ab abc b",
      map,
      alpha=0.5,
      seed=None,
      prior_map=None,
      n_trial=7,
    )
    assert_eq(probs.length(), 2)
    let mut j = 0
    while j < 2 {
      assert_true(probs[j] >= 0.0 && probs[j] <= 1.0)
      j += 1
    }
    run += 1
  }
}

///| Threshold boundary samples, injected because the baseline has no

///| entry at or below 0.1. Label:

///| `synthetic:基准 250 例中最小条目 0.1428…，无 ≤ 0.1（V-49）`.
///

///| Task 8 transfer: `_sort_probability` (`detector.py:234-237`) keeps

///| only entries with `p > PROB_THRESHOLD`; this test locks the strict

///|
/// comparison and the three bit patterns Task 8 must reuse.
fn retained_by_threshold(p : Double) -> Bool {
  p > @core.PROB_THRESHOLD
}

///|
test "threshold_boundary_samples_synthetic" {
  // Exactly 0.1 (0x3fb999999999999a), next double above, next below.
  let exact = UInt64::reinterpret_as_double(0x3FB999999999999AUL)
  let above = UInt64::reinterpret_as_double(0x3FB999999999999BUL)
  let below = UInt64::reinterpret_as_double(0x3FB9999999999999UL)
  assert_eq(exact, 0.1)
  assert_true(above > 0.1)
  assert_true(below < 0.1)
  assert_true(!retained_by_threshold(exact))
  assert_true(retained_by_threshold(above))
  assert_true(!retained_by_threshold(below))
  // As normalized entries the three patterns survive normalization: with
  // an injected [p, 1 - p] vector the sum is exactly 1.0 only for the
  // exact 0.1 sample, which is why the filter predicate above is the
  // authoritative check (Task 8 applies it to the returned vector).
  let exact_vector : Array[Double] = [exact, 0.9]
  let maxp = @core.normalize_prob(exact_vector)
  assert_eq(exact_vector[0].reinterpret_as_uint64(), 0x3FB999999999999AUL)
  assert_true(maxp > 0.0)
}
