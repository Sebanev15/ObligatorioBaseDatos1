-- Keep match sheets and goal/card events when a player leaves or is deleted.
ALTER TABLE planilla_partido
    DROP FOREIGN KEY planilla_partido_ibfk_2;
