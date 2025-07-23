-- database: ../actor.db

SELECT
    m.name,
    m.model_id,
    p.prompt_price,
    p.completion_price,
    (p.prompt_price + p.completion_price) AS total_price
FROM
    llmmodel m
JOIN
    llmmodelprice p
    ON m.id = p.llm_model_id
WHERE
    m.active = 1
    AND m.score > 0
ORDER BY
    total_price ASC;