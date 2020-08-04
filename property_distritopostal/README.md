Funcionalidad respecto a http://distritopostal.es/ 


## Municipios SIN calles (y sin códigos postales)
```
SELECT * 
FROM distritopostal_municipality AS dm
WHERE dm.id NOT IN (
SELECT DISTINCT(dw.distritopostal_municipality_id)
FROM distritopostal_way AS dw
)
AND dm.id NOT IN (
SELECT DISTINCT(dp.distritopostal_municipality_id )
FROM distritopostal_postalcode AS dp
)
ORDER BY dm.id ASC
```

## Códigos postales SIN calles
```
SELECT dp.*, dm.name, dm.url
FROM distritopostal_postalcode AS dp
LEFT JOIN distritopostal_municipality AS dm ON dp.distritopostal_municipality_id = dm.id
WHERE dp.distritopostal_municipality_id NOT IN (
SELECT DISTINCT(dw.distritopostal_municipality_id)
FROM distritopostal_way AS dw
) AND dp.distritopostal_municipality_id IN (
SELECT DISTINCT(dp.distritopostal_municipality_id)
FROM distritopostal_postalcode AS dp
)
ORDER BY dp.id ASC
```

## Crones

### Cron Check Municipalities (Distritopostal) 
Frecuencia: Manual

Descripción: Obtiene un listado de los municipios de distritopostal.es


### Cron Check Ways (Distritopostal) 
Frecuencia: Manual

Descripción: Obtiene un listado de las calles de todos los municipios / códigos postales de distritopostal.es
