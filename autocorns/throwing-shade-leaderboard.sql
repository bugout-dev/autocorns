WITH selected_paths AS (
    SELECT
        label_data -> 'args' ->> 'tokenId' as token_id,
        (label_data -> 'args' ->> 'sessionId') :: integer as session_id,
        (label_data -> 'args' ->> 'stage') :: integer as stage,
        (label_data -> 'args' ->> 'path') :: integer as path
    FROM
        polygon_labels
    WHERE
        label = 'moonworm-alpha'
        AND address = '0xDD8bf70a1f3A5557CCaB839E46cAB5533955Da65'
        AND label_data ->> 'name' = 'PathChosen'
),
correct_paths AS (
    SELECT
        (label_data -> 'args' ->> 'sessionId') :: integer as session_id,
        (label_data -> 'args' ->> 'stage') :: integer as stage,
        (label_data -> 'args' ->> 'path') :: integer as path
    FROM
        polygon_labels
    WHERE
        label = 'moonworm-alpha'
        AND address = '0xDD8bf70a1f3A5557CCaB839E46cAB5533955Da65'
        AND label_data ->> 'name' = 'PathRegistered'
),
throwing_shade_session_paths AS (
    SELECT
        token_id,
        session_id,
        stage,
        path
    FROM
        selected_paths
    WHERE
        session_id IN (2, 3, 4, 5, 6, 7)
),
throwing_shade_session_winners AS (
    SELECT
        throwing_shade_session_paths.token_id,
        throwing_shade_session_paths.session_id,
        3000 as score
    FROM
        throwing_shade_session_paths
        INNER JOIN correct_paths ON throwing_shade_session_paths.session_id = correct_paths.session_id
        AND throwing_shade_session_paths.stage = correct_paths.stage
        AND throwing_shade_session_paths.path = correct_paths.path
    WHERE
        correct_paths.stage = 5
),
throwing_shade_session_max_stages AS (
    SELECT
        token_id,
        session_id,
        max(stage) as latest_stage
    FROM
        throwing_shade_session_paths
    GROUP BY
        token_id,
        session_id
),
throwing_shade_choice_points AS (
    SELECT
        token_id,
        session_id,
        CASE
            WHEN latest_stage = 1 THEN 100
            WHEN latest_stage = 2 THEN 200
            WHEN latest_stage = 3 THEN 400
            WHEN latest_stage = 4 THEN 700
            WHEN latest_stage = 5 THEN 1200
        END as score
    FROM
        throwing_shade_session_max_stages
),
throwing_shade_point_elements AS (
    SELECT
        token_id,
        session_id,
        score
    FROM
        throwing_shade_choice_points
    UNION
    ALL
    SELECT
        token_id,
        session_id,
        score
    FROM
        throwing_shade_session_winners
),
throwing_shade_session_points AS (
    SELECT
        token_id,
        session_id,
        sum(score) as session_score
    FROM
        throwing_shade_point_elements
    GROUP BY
        token_id,
        session_id
)
SELECT
    token_id as address,
    sum(session_score) AS score,
    json_object_agg(
        'session_' || session_id :: text,
        session_score
    ) as points_data
FROM
    throwing_shade_session_points
GROUP BY
    token_id
ORDER BY
    total_score DESC,
    token_id :: integer ASC;
