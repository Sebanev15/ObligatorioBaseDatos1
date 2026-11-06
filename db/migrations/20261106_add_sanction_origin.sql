ALTER TABLE sancion_jugador
    ADD COLUMN origen ENUM('manual', 'automatica') NOT NULL DEFAULT 'manual';

UPDATE sancion_jugador
SET origen = 'automatica'
WHERE motivo IN ('roja', 'acumulacion de amarillas');
