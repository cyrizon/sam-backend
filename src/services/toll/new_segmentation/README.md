# Nouvelle stratégie de segmentation basée sur les tollways ORS

## Concept

Cette nouvelle approche utilise directement les informations `tollways` des extras ORS pour une segmentation précise et efficace.

## Workflow

1. **Récupérer la route de base** avec `extra_info: ["tollways"]`
2. **Extraire les segments tollways** depuis `route.features[0].properties.extras.tollways.values`
3. **Convertir les indices en coordonnées** géographiques
4. **Générer des polygones d'évitement** pour les segments sélectionnés
5. **Recalculer la route** avec `options.avoid_polygons`

## Structure des données tollways

```javascript
tollways: {
  summary: [
    {amount: 59.59, distance: 166890.2, value: 1},
    {amount: 40.41, distance: 113159.6, value: 0}
  ],
  values: [
    [0, 617, 0],      // segment 0-617: pas de péage (value=0)
    [617, 714, 1],    // segment 617-714: péage (value=1)
    [714, 717, 0],    // segment 714-717: pas de péage
    [717, 743, 1],    // segment 717-743: péage
    // ...
  ]
}
```

## Avantages

- ✅ Segmentation précise basée sur les données réelles d'ORS
- ✅ Pas besoin de calculer manuellement les segments 
- ✅ Coordination directe avec les indices de géométrie
- ✅ Performance optimisée (moins d'appels API)
