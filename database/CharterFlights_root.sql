USE CharterFlights;
GO

INSERT INTO AIRPORT (ICAO_CODE, IATA_CODE, NAME, CITY, COUNTRY, LATITUDE, LONGITUDE) VALUES
('KDTW', 'DTW', 'Detroit Metropolitan Wayne County Airport', 'Detroit', 'United States', 42.212400, -83.353400),
('KGRR', 'GRR', 'Gerald R. Ford International Airport', 'Grand Rapids', 'United States', 42.880800, -85.522800),
('KLAN', 'LAN', 'Capital City Airport', 'Lansing', 'United States', 42.778700, -84.587400),
('KFNT', 'FNT', 'Bishop International Airport', 'Flint', 'United States', 42.965400, -83.743600),
('KAZO', 'AZO', 'Kalamazoo/Battle Creek International Airport', 'Kalamazoo', 'United States', 42.234900, -85.552100),
('KTVC', 'TVC', 'Cherry Capital Airport', 'Traverse City', 'United States', 44.741400, -85.582200),
('KATL', 'ATL', 'Hartsfield-Jackson Atlanta International Airport', 'Atlanta', 'United States', 33.640700, -84.427700),
('KBOS', 'BOS', 'Logan International Airport', 'Boston', 'United States', 42.365600, -71.009600),
('KCLT', 'CLT', 'Charlotte Douglas International Airport', 'Charlotte', 'United States', 35.214000, -80.943100),
('KCLE', 'CLE', 'Cleveland Hopkins International Airport', 'Cleveland', 'United States', 41.411700, -81.849800),
('KORD', 'ORD', 'O''Hare International Airport', 'Chicago', 'United States', 41.974200, -87.907300),
('KDEN', 'DEN', 'Denver International Airport', 'Denver', 'United States', 39.856100, -104.673700),
('KDFW', 'DFW', 'Dallas/Fort Worth International Airport', 'Dallas', 'United States', 32.899800, -97.040300),
('KIAH', 'IAH', 'George Bush Intercontinental Airport', 'Houston', 'United States', 29.990200, -95.336800),
('KJFK', 'JFK', 'John F. Kennedy International Airport', 'New York', 'United States', 40.641300, -73.778100),
('KLAX', 'LAX', 'Los Angeles International Airport', 'Los Angeles', 'United States', 33.941600, -118.408500),
('KMCO', 'MCO', 'Orlando International Airport', 'Orlando', 'United States', 28.431200, -81.308100),
('KMIA', 'MIA', 'Miami International Airport', 'Miami', 'United States', 25.795900, -80.287000),
('KMSP', 'MSP', 'Minneapolis-Saint Paul International Airport', 'Minneapolis', 'United States', 44.884800, -93.222300),
('KPHX', 'PHX', 'Phoenix Sky Harbor International Airport', 'Phoenix', 'United States', 33.434200, -112.011600),
('KSEA', 'SEA', 'Seattle-Tacoma International Airport', 'Seattle', 'United States', 47.450200, -122.308800),
('KSFO', 'SFO', 'San Francisco International Airport', 'San Francisco', 'United States', 37.621300, -122.379000),
('KLAS', 'LAS', 'Harry Reid International Airport', 'Las Vegas', 'United States', 36.084000, -115.153700),
('KMSY', 'MSY', 'Louis Armstrong New Orleans International Airport', 'New Orleans', 'United States', 29.993400, -90.258000),
('KIND', 'IND', 'Indianapolis International Airport', 'Indianapolis', 'United States', 39.717300, -86.294400);

CREATE TABLE #Nums (n INT PRIMARY KEY);
WITH r AS (SELECT 1 AS n UNION ALL SELECT n + 1 FROM r WHERE n < 100)
INSERT INTO #Nums (n) SELECT n FROM r OPTION (MAXRECURSION 100);

INSERT INTO CREW (FIRST_NAME, LAST_NAME, LICENSE_NUMBER, ROLE)
SELECT
    CHOOSE(n % 10 + 1, 'Daniel', 'Megan', 'Sam', 'Luis', 'Priya', 'Marcus', 'Brian', 'Olivia', 'Jordan', 'Nadia'),
    CHOOSE((n * 3) % 10 + 1, 'Reyes', 'Owens', 'Ortiz', 'Herrera', 'Shah', 'Bell', 'Foster', 'Carter', 'Hale', 'Haddad'),
    'LIC-PL-' + RIGHT('000' + CAST(n AS VARCHAR(3)), 3),
    'PILOT'
FROM #Nums
WHERE n <= 40
UNION ALL
SELECT
    CHOOSE(n % 10 + 1, 'Kara', 'Jenna', 'Alex', 'Grace', 'Lauren', 'Hannah', 'Emily', 'Sofia', 'Aisha', 'Tyler'),
    CHOOSE((n * 7) % 10 + 1, 'Mills', 'Pryor', 'Dunn', 'Lin', 'Kim', 'Wolfe', 'Connell', 'Rossi', 'Patel', 'Morgan'),
    'LIC-FA-' + RIGHT('000' + CAST(n AS VARCHAR(3)), 3),
    'FLIGHT ATTENDANT'
FROM #Nums
WHERE n <= 40;

SELECT ROW_NUMBER() OVER (ORDER BY AIRPORT_ID) - 1 AS rn, AIRPORT_ID AS id
INTO #Ap
FROM dbo.AIRPORT;

SELECT
    ROW_NUMBER() OVER (ORDER BY k.n, r.n) AS cycle_no,
    k.n AS k,
    r.n AS r,
    CASE WHEN k.n % 5 = 0 THEN 5 ELSE 25 END AS T
INTO #Cycles
FROM (SELECT n FROM #Nums WHERE n <= 24) AS k
CROSS JOIN (SELECT n - 1 AS n FROM #Nums WHERE n <= 5) AS r
WHERE (k.n % 5 <> 0 AND r.n = 0) OR (k.n % 5 = 0);

SELECT
    c.cycle_no,
    c.k,
    t.n - 1 AS t,
    (c.r + (t.n - 1) * c.k) % 25 AS origin_rn,
    (c.r + t.n * c.k) % 25 AS dest_rn
INTO #Legs
FROM #Cycles c
CROSS JOIN (SELECT n FROM #Nums WHERE n <= 25) AS t
WHERE t.n - 1 < c.T;

INSERT INTO FLIGHT (FLIGHT_NUMBER, ORIGIN_AIRPORT_ID, DESTINATION_AIRPORT_ID, DEPARTURE_DATETIME, ARRIVAL_DATETIME, AIRCRAFT_TAIL_NUMBER, AIRCRAFT_TYPE, SEAT_CAPACITY)
SELECT
    'CH' + RIGHT('0000' + CAST(ROW_NUMBER() OVER (ORDER BY l.cycle_no, l.t) AS VARCHAR(4)), 4),
    o.id,
    d.id,
    DATEADD(MINUTE, (l.t / 4) * 1440 + 420 + (l.t % 4) * 150, '2026-12-05 00:00'),
    DATEADD(MINUTE, (l.t / 4) * 1440 + 420 + (l.t % 4) * 150 + 90, '2026-12-05 00:00'),
    'N' + RIGHT('000' + CAST(l.cycle_no AS VARCHAR(3)), 3) + 'CH',
    CHOOSE(l.cycle_no % 3 + 1, 'Citation CJ3', 'King Air 350', 'Learjet 45'),
    CHOOSE(l.cycle_no % 3 + 1, 8, 9, 6)
FROM #Legs l
INNER JOIN #Ap o ON o.rn = l.origin_rn
INNER JOIN #Ap d ON d.rn = l.dest_rn;

INSERT INTO ASSIGNMENT (FLIGHT_ID, CREW_ID)
SELECT f.FLIGHT_ID, c.CREW_ID
FROM FLIGHT f
INNER JOIN CREW c
    ON c.LICENSE_NUMBER IN (
        'LIC-PL-' + SUBSTRING(f.AIRCRAFT_TAIL_NUMBER, 2, 3),
        'LIC-FA-' + SUBSTRING(f.AIRCRAFT_TAIL_NUMBER, 2, 3)
    );

SELECT
    f.FLIGHT_ID,
    s.s,
    ROW_NUMBER() OVER (ORDER BY f.FLIGHT_ID, s.s) AS seq
INTO #Seats
FROM FLIGHT f
CROSS JOIN (VALUES (1), (2), (3), (4)) AS s (s);

INSERT INTO PASSENGER (FIRST_NAME, LAST_NAME, EMAIL, PHONE)
SELECT
    CHOOSE(seq % 20 + 1, 'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda', 'David', 'Elizabeth',
           'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen'),
    CHOOSE((seq * 7) % 20 + 1, 'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
           'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'),
    'pax' + CAST(seq AS VARCHAR(6)) + '@example.com',
    CASE WHEN seq % 3 = 0 THEN NULL ELSE '555-' + RIGHT('0000' + CAST(seq % 10000 AS VARCHAR(4)), 4) END
FROM #Seats;

INSERT INTO BOOKING (PASSENGER_ID, FLIGHT_ID, SEAT_NUMBER)
SELECT p.PASSENGER_ID, s.FLIGHT_ID, CHOOSE(s.s, '1A', '1B', '1C', '1D')
FROM #Seats s
INNER JOIN PASSENGER p
    ON p.EMAIL = 'pax' + CAST(s.seq AS VARCHAR(6)) + '@example.com';

DROP TABLE #Seats, #Legs, #Cycles, #Ap, #Nums;
GO