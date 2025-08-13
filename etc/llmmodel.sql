PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE llmmodel (
	id VARCHAR NOT NULL, 
	created_at INTEGER, 
	updated_at INTEGER, 
	name VARCHAR NOT NULL, 
	model_id VARCHAR NOT NULL, 
	canonical_id VARCHAR, 
	active BOOLEAN NOT NULL, 
	notes VARCHAR, 
	supports_json BOOLEAN NOT NULL, 
	supports_schema BOOLEAN NOT NULL, 
	score INTEGER NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO llmmodel VALUES('Needy-CLOSE-walk-Half-Pros',1752614406,1752614406,'aion','openrouter/aion-labs/aion-1.0','aion-labs/aion-1.0',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('taste-Water-WHARF-street-Toe',1752614406,1752614406,'aion-mini','openrouter/aion-labs/aion-1.0-mini','aion-labs/aion-1.0-mini',1,'',0,0,0);
INSERT INTO llmmodel VALUES('bitter-RECENT-Weapon-Limit-DREARY',1752614406,1752614406,'aion-rp','openrouter/aion-labs/aion-rp-llama-3.1-8b','aion-labs/aion-rp-llama-3.1-8b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('verbs-Jail-Awful-Wing-doll',1752614406,1752614406,'anubis','openrouter/thedrummer/anubis-pro-105b-v1','thedrummer/anubis-pro-105b-v1',1,'',0,0,0);
INSERT INTO llmmodel VALUES('spotty-Cobweb-Chief-Beef-Nuclei',1752614406,1752614406,'celeste','openrouter/nothingiisreal/mn-celeste-12b','nothingiisreal/mn-celeste-12b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('peace-Window-Joys-dirty-SIMPLE',1752614406,1752614406,'chatgpt','gpt-3.5-turbo','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('FLASH-Misco-side-bent-Claim',1752614406,1752614406,'chatgpt-16k','3.5-16k,gpt-3.5-turbo-16k','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('USEFUL-FALCON-ELATED-puffy-Real',1752614406,1752614406,'chatgpt-4o','chatgpt-4o-latest','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('beos-Echo-DIRT-liquid-Bronze',1752614406,1752614406,'claude-3.5','openrouter/anthropic/claude-3.7-sonnet','anthropic/claude-3-7-sonnet-20250219',0,'Model is too expensive, disabled by system',0,1,10);
INSERT INTO llmmodel VALUES('BIKE-Wave-diver-Ting-Engine',1752614406,1752614406,'claude-sonnet-4','openrouter/anthropic/claude-sonnet-4','anthropic/claude-4-sonnet-20250522',0,'Model is too expensive, disabled by system',0,1,10);
INSERT INTO llmmodel VALUES('DRAWER-AMOUNT-Water-Romano-cloth',1752614406,1752614406,'clauee-opus-4','openrouter/anthropic/claude-opus-4','anthropic/claude-4-opus-20250522',0,'Model is too expensive, disabled by system',0,1,10);
INSERT INTO llmmodel VALUES('TACIT-Roll-Blaze-PAN-Expect',1752614406,1752614406,'command-a','openrouter/cohere/command-a','cohere/command-a-03-2025',0,'Model is too expensive, disabled by system',1,0,10);
INSERT INTO llmmodel VALUES('mice-corn-ABRUPT-Ask-BEEF',1752614406,1752614406,'deepcoder','openrouter/agentica-org/deepcoder-14b-preview:free','agentica-org/deepcoder-14b-preview',1,'',0,0,0);
INSERT INTO llmmodel VALUES('Cold-HAIR-Warmth-Add-Mask',1752614406,1752614406,'deepseek','openrouter/deepseek/deepseek-chat-v3-0324','deepseek/deepseek-chat-v3-0324',1,'',1,1,20);
INSERT INTO llmmodel VALUES('PRION-SUMMER-blush-Test-Scarf',1752614406,1752614406,'deepseek-free','openrouter/deepseek/deepseek-chat-v3-0324:free','deepseek/deepseek-chat-v3-0324',1,'',0,1,10);
INSERT INTO llmmodel VALUES('amused-Strap-SHAGGY-Zebra-YORUBA',1752614406,1752614406,'deepseek-r1','deepseek-r1:8b','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('Houses-potato-Cruel-Bumper-Ting',1752614406,1752614406,'dolphin3','dolphin3:latest','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SIDER-Amount-Unit-Debt-CAPPS',1752614406,1752614406,'dolphin-24','openrouter/cognitivecomputations/dolphin3.0-r1-mistral-24b:free','cognitivecomputations/dolphin3.0-r1-mistral-24b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('VERSE-groan-hydro-CYRIL-CLOSED',1752614406,1752614406,'drummer','openrouter/thedrummer/valkyrie-49b-v1','thedrummer/valkyrie-49b-v1',1,'',1,0,10);
INSERT INTO llmmodel VALUES('pink-tempo-Part-MARKED-Third',1752614406,1752614406,'euryale','openrouter/sao10k/l3.3-euryale-70b','sao10k/l3.3-euryale-70b-v2.3',1,'',1,0,10);
INSERT INTO llmmodel VALUES('PURE-Rein-Marine-Frog-annan',1752614406,1752614406,'euryale-3.1','openrouter/sao10k/l3.1-euryale-70b','sao10k/l3.1-euryale-70b',1,'',1,0,10);
INSERT INTO llmmodel VALUES('love-Look-rejoin-ace-nosy',1752614406,1752614406,'eva','openrouter/eva-unit-01/eva-llama-3.33-70b','eva-unit-01/eva-llama-3.33-70b',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('vigor-Siding-Corn-salary-Broth',1752614406,1752614406,'eva-qwen','openrouter/eva-unit-01/eva-qwen-2.5-32b','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('rejoin-FRAIL-Injure-Bow-Tub',1752614406,1752614406,'fimbulvetr','openrouter/sao10k/fimbulvetr-11b-v2','sao10k/fimbulvetr-11b-v2',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SUIT-tyra-cloth-Luck-Wire',1752614406,1752614406,'gemini-2.5-flash','openrouter/google/gemini-2.5-flash','google/gemini-2.5-flash',1,'',1,1,20);
INSERT INTO llmmodel VALUES('MANDA-Digi-fseek-memory-Dime',1752614406,1752614406,'gemini-2.5-pro','openrouter/google/gemini-2.5-pro','google/gemini-2.5-pro',1,'',1,1,20);
INSERT INTO llmmodel VALUES('war-SNAKE-car-Snakes-Elf',1752614406,1752614406,'gemini2-5-thinking','openrouter/google/gemini-2.5-flash-preview:thinking','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('FIT-Cloth-file-jeans-Hall',1752614406,1752614406,'glm-32b','openrouter/thudm/glm-z1-32b:free','thudm/glm-z1-32b-0414',1,'',0,0,0);
INSERT INTO llmmodel VALUES('quick-toric-KRAZY-dress-Bluey',1752614406,1752614406,'gpt-4.5','gpt-4.5-preview','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('FAINT-Fetch-Steam-Jeux-IDOL',1752614406,1752614406,'gpt4','gpt-4','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('VESSEL-MUON-Gifted-Mark-BURY',1752614406,1752614406,'gpt4.1','openrouter/openai/gpt-4.1','openai/gpt-4.1-2025-04-14',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('Quack-shame-Twig-stmt-TOMMY',1752614406,1752614406,'gpt4.1-mini','openrouter/openai/gpt-4.1-mini','openai/gpt-4.1-mini-2025-04-14',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Label-setenv-PLANTS-Equal-ULTIMO',1752614407,1752614407,'gpt4.1-nano','openrouter/openai/gpt-4.1-nano','openai/gpt-4.1-nano-2025-04-14',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Stuff-Fancy-Craven-Saber-sore',1752614407,1752614407,'gpt4o','gpt-4o','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('FOREST-POISED-inform-story-awful',1752614407,1752614407,'gpt4o-mini','gpt-4o-mini','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('sign-Order-overt-Two-grey',1752614407,1752614407,'grok3','openrouter/x-ai/grok-3','x-ai/grok-3',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('TIDY-AXONS-Glover-range-seed',1752614407,1752614407,'grok3-mini','openrouter/x-ai/grok-3-mini','x-ai/grok-3-mini',1,'',1,1,20);
INSERT INTO llmmodel VALUES('family-Vast-large-lands-Bell',1752614407,1752614407,'haiku','openrouter/anthropic/claude-3.5-haiku','anthropic/claude-3-5-haiku',1,'',0,1,10);
INSERT INTO llmmodel VALUES('Loud-atomic-Seed-RELIC-Mighty',1752614407,1752614407,'hermes','openrouter/nousresearch/deephermes-3-llama-3-8b-preview:free','nousresearch/deephermes-3-llama-3-8b-preview',1,'',0,0,0);
INSERT INTO llmmodel VALUES('toad-blitz-Used-Sin-CRUX',1752614407,1752614407,'infermatic','openrouter/infermatic/mn-inferor-12b','infermatic/mn-inferor-12b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('gaping-TOAD-ULTRA-RHYME-Tall',1752614407,1752614407,'inflection','openrouter/inflection/inflection-3-pi','inflection/inflection-3-pi',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('cleric-Drum-NOUNS-PLANTS-Intend',1752614407,1752614407,'inflection-productivity','openrouter/inflection/inflection-3-productivity','inflection/inflection-3-productivity',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('angle-slap-Birth-permit-FAGAN',1752614407,1752614407,'kimi','openrouter/moonshotai/kimi-dev-72b:free','moonshotai/kimi-dev-72b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SKIRT-pasted-wreck-Food-REEF',1752614407,1752614407,'kimi-thinking','openrouter/moonshotai/kimi-vl-a3b-thinking:free','moonshotai/kimi-vl-a3b-thinking',1,'',0,0,0);
INSERT INTO llmmodel VALUES('HYDRO-DAMAGE-EFFECT-Tray-dead',1752614407,1752614407,'liquid','openrouter/liquid/lfm-40b','liquid/lfm-40b',1,'',1,0,10);
INSERT INTO llmmodel VALUES('MILKY-Add-Jeux-HANDS-stay',1752614407,1752614407,'ll4-maverick','openrouter/meta-llama/llama-4-maverick','meta-llama/llama-4-maverick-17b-128e-instruct',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Paper-border-Slim-Kettle-array',1752614407,1752614407,'ll4-scout','openrouter/meta-llama/llama-4-scout','meta-llama/llama-4-scout-17b-16e-instruct',1,'',1,1,20);
INSERT INTO llmmodel VALUES('STAMP-Benz-many-Faded-Maurer',1752614407,1752614407,'llama-3.3','openrouter/nvidia/llama-3.3-nemotron-super-49b-v1:free','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('STUPID-Pine-last-noord-elite',1752614407,1752614407,'llama-4-maverick','openrouter/meta-llama/llama-4-maverick:free','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('like-Hover-Telly-Earch-Lysis',1752614407,1752614407,'llama-4-scout','openrouter/meta-llama/llama-4-scout:free','',0,'Model is no longer available in OpenRouter API',0,0,0);
INSERT INTO llmmodel VALUES('deer-Serve-WITTY-parcel-Launch',1752614407,1752614407,'magistral-medium','openrouter/mistralai/magistral-medium-2506','mistralai/magistral-medium-2506',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('land-LIVE-Tacit-BRIGHT-Rebel',1752614407,1752614407,'magistral-small','openrouter/mistralai/magistral-small-2506','mistralai/magistral-small-2506',1,'',1,1,20);
INSERT INTO llmmodel VALUES('Meat-DUBLIN-nerdy-Nerdy-narrow',1752614407,1752614407,'magnum','openrouter/anthracite-org/magnum-v4-72b','anthracite-org/magnum-v4-72b',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('mori-Boot-SORTS-burch-EMMET',1752614407,1752614407,'midnight-rose','openrouter/sophosympatheia/midnight-rose-70b','sophosympatheia/midnight-rose-70b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('expres-Pixie-MOVING-Visit-EARTHY',1752614407,1752614407,'minimax','openrouter/minimax/minimax-m1','minimax/minimax-m1',1,'',0,1,10);
INSERT INTO llmmodel VALUES('lace-Array-airing-Show-COOING',1752614407,1752614407,'mistral-small','openrouter/mistralai/mistral-small-3.1-24b-instruct:free','mistralai/mistral-small-3.1-24b-instruct-2503',1,'',1,1,20);
INSERT INTO llmmodel VALUES('PLACE-Bang-Travel-Earthy-tender',1752614407,1752614407,'o3','openrouter/openai/o3','openai/o3-2025-04-16',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('MICE-NIPPLE-Lumpy-Admit-Club',1752614407,1752614407,'o3-hi','openrouter/openai/o3-mini-high','openai/o3-mini-high-2025-01-31',1,'',1,1,20);
INSERT INTO llmmodel VALUES('wound-CRAVEN-Rock-HELM-Fuzzy',1752614407,1752614407,'o4-hi','openrouter/openai/o4-mini-high','openai/o4-mini-high-2025-04-16',1,'',1,1,20);
INSERT INTO llmmodel VALUES('occur-Word-Gabby-HELP-slow',1752614407,1752614407,'o4-mini','openrouter/openai/o4-mini','openai/o4-mini-2025-04-16',1,'',1,1,20);
INSERT INTO llmmodel VALUES('gate-Errata-dohc-ABRUPT-Bite',1752614407,1752614407,'open-4o-mini','openrouter/openai/gpt-4o-mini','openai/gpt-4o-mini',1,'',1,1,20);
INSERT INTO llmmodel VALUES('bead-Kemp-AZTEC-Slow-stone',1752614407,1752614407,'qwen','openrouter/qwen/qwen-max','qwen/qwen-max-2025-01-25',0,'Model is too expensive, disabled by system',1,1,20);
INSERT INTO llmmodel VALUES('FLAG-Duarte-dwarf-Porter-wobble',1752614407,1752614407,'qwen3','qwen3:8b','',1,'',0,0,0);
INSERT INTO llmmodel VALUES('common-Bathe-Simi-World-relic',1752614407,1752614407,'qwen3-14b','openrouter/qwen/qwen3-14b:free','qwen/qwen3-14b-04-28',1,'',0,0,0);
INSERT INTO llmmodel VALUES('MAKER-towing-elf-JAR-POKING',1752614407,1752614407,'qwen3-30b','openrouter/qwen/qwen3-30b-a3b:free','qwen/qwen3-30b-a3b-04-28',1,'',0,0,0);
INSERT INTO llmmodel VALUES('rotten-DILL-telly-ELDER-Square',1752614407,1752614407,'qwen3-32b','openrouter/qwen/qwen3-32b:free','qwen/qwen3-32b-04-28',1,'',0,0,0);
INSERT INTO llmmodel VALUES('beast-Women-SON-uppity-POTTS',1752614407,1752614407,'qwerky','openrouter/featherless/qwerky-72b:free','featherless/qwerky-72b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('WING-river-TRAIN-Jeans-POP',1752614407,1752614407,'qwq','openrouter/arliai/qwq-32b-arliai-rpr-v1:free','arliai/qwq-32b-arliai-rpr-v1',1,'',0,0,0);
INSERT INTO llmmodel VALUES('Female-knock-Corner-zombie-Riken',1752614407,1752614407,'reka','openrouter/rekaai/reka-flash-3:free','rekaai/reka-flash-3',1,'',0,0,0);
INSERT INTO llmmodel VALUES('SADDLE-Books-Wall-cherry-nipple',1752614407,1752614407,'rocinante','openrouter/thedrummer/rocinante-12b','thedrummer/rocinante-12b',1,'',1,1,20);
INSERT INTO llmmodel VALUES('SQUASH-ICKY-RELIC-TURN-marine',1752614407,1752614407,'shisa','openrouter/shisa-ai/shisa-v2-llama3.3-70b:free','shisa-ai/shisa-v2-llama3.3-70b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('VAULT-CYRIL-Cosmic-Crook-SHAKY',1752614407,1752614407,'skyfall','openrouter/thedrummer/skyfall-36b-v2','thedrummer/skyfall-36b-v2',1,'',1,0,10);
INSERT INTO llmmodel VALUES('HAMMER-PLUG-Swing-Salad-Kid',1752614407,1752614407,'sorcerer','openrouter/raifle/sorcererlm-8x22b','raifle/sorcererlm-8x22b',0,'Model is too expensive, disabled by system',0,0,0);
INSERT INTO llmmodel VALUES('stuff-crush-Plucky-icky-zany',1752614407,1752614407,'starcannon','openrouter/aetherwiing/mn-starcannon-12b','aetherwiing/mn-starcannon-12b',1,'',0,0,0);
INSERT INTO llmmodel VALUES('rice-charge-mark-summer-Smudge',1752614407,1752614407,'unslop-nemo','openrouter/thedrummer/unslopnemo-12b','thedrummer/unslopnemo-12b',1,'',1,1,20);
COMMIT;
