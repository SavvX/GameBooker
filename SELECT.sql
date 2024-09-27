WITH RankedReservations AS (
    SELECT 
        device, 
        date AS last_date, 
        name, 
        pin_hash,
        ROW_NUMBER() OVER (PARTITION BY device ORDER BY date DESC) AS row_num
    FROM 
        Reservation
)

SELECT 
    device, 
    last_date, 
    name, 
    pin_hash
FROM 
    RankedReservations
WHERE 
    row_num = 1;
