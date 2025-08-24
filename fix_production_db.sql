-- Fix missing columns in workout_plans table for production
-- Run this in Render Shell: render shell

-- Add missing columns if they don't exist
DO $$
BEGIN
    -- Add goal column if missing (extend existing if too small)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name='workout_plans' AND column_name='goal') THEN
        ALTER TABLE workout_plans ADD COLUMN goal VARCHAR(200) DEFAULT 'Персональный план тренировок';
        UPDATE workout_plans SET goal = 'Персональный план тренировок' WHERE goal IS NULL;
        ALTER TABLE workout_plans ALTER COLUMN goal SET NOT NULL;
        RAISE NOTICE 'Added goal column';
    ELSE
        -- Check if existing goal column is too small
        IF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name='workout_plans' AND column_name='goal' 
                  AND character_maximum_length < 200) THEN
            ALTER TABLE workout_plans ALTER COLUMN goal TYPE VARCHAR(200);
            RAISE NOTICE 'Extended goal column to VARCHAR(200)';
        END IF;
    END IF;

    -- Add description column if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name='workout_plans' AND column_name='description') THEN
        ALTER TABLE workout_plans ADD COLUMN description TEXT DEFAULT '';
        ALTER TABLE workout_plans ALTER COLUMN description SET NOT NULL;
        RAISE NOTICE 'Added description column';
    END IF;

    -- Add motivation_text column if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name='workout_plans' AND column_name='motivation_text') THEN
        ALTER TABLE workout_plans ADD COLUMN motivation_text TEXT DEFAULT '';
        ALTER TABLE workout_plans ALTER COLUMN motivation_text SET NOT NULL;
        RAISE NOTICE 'Added motivation_text column';
    END IF;

    -- Add user_analysis column if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name='workout_plans' AND column_name='user_analysis') THEN
        ALTER TABLE workout_plans ADD COLUMN user_analysis JSONB DEFAULT '{}';
        ALTER TABLE workout_plans ALTER COLUMN user_analysis SET NOT NULL;
        RAISE NOTICE 'Added user_analysis column';
    END IF;

    -- Add long_term_strategy column if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name='workout_plans' AND column_name='long_term_strategy') THEN
        ALTER TABLE workout_plans ADD COLUMN long_term_strategy JSONB DEFAULT '{}';
        ALTER TABLE workout_plans ALTER COLUMN long_term_strategy SET NOT NULL;
        RAISE NOTICE 'Added long_term_strategy column';
    END IF;

END $$;

-- Verify the changes
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'workout_plans'
AND column_name IN ('goal', 'description', 'motivation_text', 'user_analysis', 'long_term_strategy')
ORDER BY column_name;