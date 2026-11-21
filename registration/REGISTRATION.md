# Registration record (not published)

- Code commit: `24b614aa29c3786dace92955f93c2317bf44581a`
- Concordia: v1.8.9, commit `3643ac0466f748b8055b61feb0b7908411f73d84`
- Agent zip: 4,537,615 bytes, SHA-256 `e9ffb65167d776fd4beae14ee65cd3b44ec9c489870698c203f7acdefc199582`

## Models

- google/gemma-2-9b-it at revision `11c9b309abf73637e4b6f9a3fa1e92e615547819`
  - `model-00001-of-00004.safetensors`: `a0d4eb4fcbddfe01b0dc7a58386a3980826ededaf0ecd67d1ef38995b89615ba`
  - `model-00002-of-00004.safetensors`: `712a589c333f49f7b6f3870838a9e0ab4b3c0260abd5130e8c54316e6c99640b`
  - `model-00003-of-00004.safetensors`: `5a9f84eb9846840802200c6502ccaaebf0a146ee89dcb8822fab795c392dd667`
  - `model-00004-of-00004.safetensors`: `3349b4960bbc0bf7e47a624e5c520881adb06e2da4bda6ed14b51c7f647fe26c`
- google/gemma-2-2b-it at revision `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`
  - `model-00001-of-00002.safetensors`: `532d792c9178805064170a3ec485b7dedbfccc6fd297b92c31a6091b6c7e41bf`
  - `model-00002-of-00002.safetensors`: `6d6d9ce84db398fb6e0191f91542e5da0a73da2cb695e172a24edc2146dc8d20`
- sentence-transformers/all-mpnet-base-v2 at revision `e8c3b32edf5434bc2275fc9bab85f82640a19130`
  - `model.safetensors`: `78c0197b6159d92658e319bc1d72e4c73a9a03dd03815e70e555c5ef05615658`

## Hardware

- **Bank-generation and development hardware:** NVIDIA A10G (23028 MiB), driver 595.112.07, torch 2.4.1+cu121, CUDA (torch.version.cuda) 12.1, cuDNN 90100; AWS g5.xlarge (4 vCPUs, 16 GB RAM).
- **Confirmatory hardware:** to be decided. PROTOCOL.md section 3 specifies one 48 GB GPU; exact repeatability (P0.7) is required on that configuration only.

## Memory banks (SHA-256)

- `formative_v01.parquet`: `036088e9e1950a5290e860564893b0e19c23835f51bc605d225890dd69d3d151`
- `formative_v02.parquet`: `5ac0a0ceac0b0fbcb303c79893e30ba76c2f56a525cfc7f9ef2913b0dd134483`
- `formative_v03.parquet`: `3e65402bcf2bd7649493f647e09eacf08911594e2412885bc13787f8969536f0`
- `formative_v04.parquet`: `95e2c03f2f767a507bb4371412721ee31fe92554ad7a0018f1c68bdacedff206`
- `formative_v05.parquet`: `dd61cd28ee13fd4cc079f32f9bcc719f170eceb53564a020dd4b648d2e34e43e`
- `formative_v06.parquet`: `97f9cde9bdd78a348d3e133014c42247b8acb2a20bca47c5bb91c81d076b58b6`
- `formative_v07.parquet`: `4be541713b55ac9cce041f332503f1bff8ba0262151fffe9a04b20d428768708`
- `formative_v08.parquet`: `1c28950e1341b60248bc914cd0d02ce29a30fcf5c527ac8032cf68d5f6efed21`
- `formative_v09.parquet`: `f76a332b54b7a5bf77ea780cce4361fcebbf7fdaad85e6f6ab4602e214b701bd`
- `formative_v10.parquet`: `6c9440eb2e2d09a93b72080e6bffd7346152d46cda46eb755341f65fac436ce6`
- `formative_v11.parquet`: `ca1d3cae5be2606276288aa7b3fb1af965e67a66c4bb0f8a465a4a1ed3ce9286`
- `formative_v12.parquet`: `d65838a2ffeadacf7c9e92ad13a3d269734c3dd550e88accda2114458b74afaa`
- `formative_v13.parquet`: `32d084fa109e14b2a3d4a7a31bf16983058ecf24407f3befb68d16684d12eca0`
- `formative_v14.parquet`: `ac22fe3bd9fd92c44be8fedc0fd27ddba5e653c6b854061766d707b522d9e66a`

## requirements.gpu.lock

- `dd0493f98b5732b88e237835556087ddba93255f5931488ac2aa53d253e7f4b8`

## Code files (SHA-256 at the code commit)

- `.gitignore`: `abf84c97712f740a98fafb4e3f9f29fd6e93d0f79ce5d3aea39c3fa48de4cea8`
- `PROTOCOL.md`: `0344f2683075f55b7cec25fc1f649fb33b2998ddaaaea3ef73524ea9511cea63`
- `refimpl/__init__.py`: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `refimpl/analysis.py`: `6240775b7e99828a90459350ab32d384aad20c3ec10784785fea301efdf09236`
- `refimpl/conditions.py`: `5ef03b6d0092b444a8e0c234c64ae381ea80cea872174e8331bd95ba32ad2c60`
- `refimpl/core.py`: `7a83fa03261cf843fa3ed9f7b83791af61189075a8176d7d41b2f74a96a775d8`
- `refimpl/determinism.py`: `456410b6c3d87abfe3257a23393ee7a24e6b7841d94d36877cece63ab14856b8`
- `refimpl/local_gemma2.py`: `b208c96c41bd0d925da477770e9f69d1ba97c55a40bca12deb922231b139acd5`
- `refimpl/phase2.py`: `35b400ca2590b46feec15a8a5b4f14577f829598776f1af2056971df37430940`
- `refimpl/phase3.py`: `582b6bf35b1f77b0272a09c1700ba269a74b20fcbbf4b01c304ae7cb73846def`
- `refimpl/pipeline.py`: `0b2efb45ec48322b5c6711bff1f754148958441ae289d05797d525d550ac7bb5`
- `refimpl/runtime.py`: `602e9697f76d00f35520c2a1c1a664df819c60ada774499aaca542bf33387319`
- `refimpl/steering.py`: `d00c0e88fa5beaf8f3e25ff42e2213a6d7f52ec1c84650e60921ca5d82187540`
- `requirements.gpu.lock`: `dd0493f98b5732b88e237835556087ddba93255f5931488ac2aa53d253e7f4b8`
- `requirements.lock`: `b6ad400b494bf2782498212489e49a414756286f4721a8c537d08fec3f714741`
- `scripts/check_phase2_agents.py`: `2fd195dc92228c0082bbdd84e5726aeb42f50f886fe9aaed85cca53d2686d3e9`
- `scripts/check_phase3_memory.py`: `a0690095a6c1d2ee59917a276372107216e8107b537b22a173d456551d03c5aa`
- `scripts/download_models.py`: `8f58e820319d113b363065dbfe6824719e63a107eb9fb8aecfa1dc7ac07f1cd3`
- `scripts/generate_banks.py`: `a2c9000f147bf76850737ae2b283b7c1d0a40e3d121f6848e65943a41b1f4875`
- `scripts/make_registration.py`: `b75bfef4643df426284bd9e569b5e6ca165e6b2a0db335475e9a43df2507315e`
- `scripts/nonet.sh`: `4cc65aeb7f9d213163e2474afecfce2e612f9dca831abc80c799c5cc9911f067`
- `tests/scoring_orders.py`: `374aabdac67826f682ceb33979106d5f0d466c3b8be62bea9c7871fdd26653b4`
- `tests/smoke_gemma.py`: `65f45d06b792958c3b3a682eebafe1dc641a99350aa22bf6b162d60824a4e86a`
- `tests/smoke_phase2.py`: `ec8b6ecc64ec24772d81685756da23b03965013ec6fd08372498d4625bdc8750`
- `tests/test_banks.py`: `06d068b21007d8e5d7d90665b2e016818e5a8c839fdf94a18d00293bdc1cf990`
- `tests/test_core.py`: `7c329b3f69f32bd24ac24b8283386cc5c8005c2d364691c189b2c8d564b7d1f8`
- `tests/test_design.py`: `3d8c521b30731a1c8757f0bc47f2c5e6b4959729a530e05eda42cd50ac07faf1`
