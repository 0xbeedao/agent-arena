PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE llmmodelstats (
	id VARCHAR NOT NULL, 
	created_at INTEGER, 
	updated_at INTEGER, 
	llm_model_id INTEGER NOT NULL, 
	eval_type VARCHAR NOT NULL, 
	run_id VARCHAR, 
	duration_ms INTEGER, 
	success BOOLEAN, 
	error_message VARCHAR, 
	timestamp INTEGER, 
	extra VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(llm_model_id) REFERENCES llmmodel (id)
);
COMMIT;
