"""
toll_avoidance_analyzer.py
--------------------------

Responsabilité : Analyser quels péages peuvent être évités et dans quel ordre.
Gère la logique d'analyse et de priorisation des péages à éviter.
"""

from itertools import combinations


class TollAvoidanceAnalyzer:
    """
    Analyseur d'évitement de péages.
    Responsabilité unique : déterminer les stratégies d'évitement optimales.
    """
    
    def __init__(self):
        pass
    
    def analyze_avoidance_opportunities(self, base_tolls, max_tolls):
        """
        Analyse les opportunités d'évitement pour optimiser une route.
        
        Args:
            base_tolls: Péages de la route de base
            max_tolls: Nombre maximum de péages autorisés
            
        Returns:
            list: Combinaisons d'évitement triées par priorité
        """
        if len(base_tolls) <= max_tolls:
            print(f"✅ Route de base OK: {len(base_tolls)} ≤ {max_tolls} péages")
            return []
        
        print(f"🔍 Analyse d'évitement: {len(base_tolls)} péages → max {max_tolls}")
        
        # Générer toutes les combinaisons d'évitement possibles
        avoidance_combinations = []
        
        # Pour chaque nombre de péages à éviter (de 1 à n)
        min_to_avoid = len(base_tolls) - max_tolls
        max_to_avoid = len(base_tolls) - 1  # Garder au moins 1 péage
        
        for num_to_avoid in range(min_to_avoid, max_to_avoid + 1):
            if num_to_avoid > 0:
                # Générer toutes les combinaisons de ce nombre
                for tolls_to_avoid in combinations(base_tolls, num_to_avoid):
                    avoidance_combinations.append({
                        'tolls_to_avoid': list(tolls_to_avoid),
                        'expected_tolls': len(base_tolls) - num_to_avoid,
                        'priority': self._calculate_priority(tolls_to_avoid, base_tolls)
                    })
        
        # Trier par priorité (plus prioritaire en premier)
        avoidance_combinations.sort(key=lambda x: x['priority'], reverse=True)
        
        print(f"📊 {len(avoidance_combinations)} combinaisons d'évitement générées")
        return avoidance_combinations
    
    def _calculate_priority(self, tolls_to_avoid, base_tolls):
        """
        Calcule la priorité d'une combinaison d'évitement.
        Plus la priorité est élevée, plus la combinaison est intéressante à tester en premier.
        
        Args:
            tolls_to_avoid: Péages à éviter
            base_tolls: Tous les péages de la route de base
            
        Returns:
            float: Score de priorité
        """
        priority = 0.0
        
        # 1. Favoriser l'évitement de moins de péages (plus facile à réaliser)
        priority += (len(base_tolls) - len(tolls_to_avoid)) * 10
        
        # 2. Favoriser l'évitement des péages les plus coûteux
        for toll in tolls_to_avoid:
            toll_cost = toll.get('cost', 0)
            priority += toll_cost * 2
        
        # 3. Favoriser l'évitement des péages en début/fin de route (plus faciles à contourner)
        for i, toll in enumerate(base_tolls):
            if toll in tolls_to_avoid:
                if i == 0 or i == len(base_tolls) - 1:  # Premier ou dernier péage
                    priority += 5
                elif i == 1 or i == len(base_tolls) - 2:  # Deuxième ou avant-dernier
                    priority += 3
        
        # 4. Favoriser l'évitement des péages "ouverts" (souvent plus faciles à éviter)
        for toll in tolls_to_avoid:
            if toll.get('role') == 'O':  # Péage ouvert
                priority += 2
        
        return priority
    
    def get_single_toll_avoidance_priority(self, base_tolls):
        """
        Retourne l'ordre de priorité pour éviter les péages un par un.
        
        Args:
            base_tolls: Péages de la route de base
            
        Returns:
            list: Péages triés par priorité d'évitement (plus prioritaire en premier)
        """
        if not base_tolls:
            return []
        
        # Calculer la priorité de chaque péage individuel
        toll_priorities = []
        for i, toll in enumerate(base_tolls):
            priority = self._calculate_single_toll_priority(toll, i, len(base_tolls))
            toll_priorities.append({
                'toll': toll,
                'priority': priority,
                'position': i
            })
        
        # Trier par priorité décroissante
        toll_priorities.sort(key=lambda x: x['priority'], reverse=True)
        
        return [item['toll'] for item in toll_priorities]
    
    def _calculate_single_toll_priority(self, toll, position, total_tolls):
        """
        Calcule la priorité d'évitement d'un péage individuel.
        
        Args:
            toll: Péage à analyser
            position: Position du péage dans la route (0-indexé)
            total_tolls: Nombre total de péages
            
        Returns:
            float: Score de priorité
        """
        priority = 0.0
        
        # 1. Coût du péage (plus cher = plus prioritaire à éviter)
        priority += toll.get('cost', 0) * 3
        
        # 2. Position dans la route (extrémités plus faciles à éviter)
        if position == 0 or position == total_tolls - 1:  # Premier ou dernier
            priority += 10
        elif position == 1 or position == total_tolls - 2:  # Proche des extrémités
            priority += 5
        else:  # Au milieu
            priority += 1
        
        # 3. Type de péage (ouverts plus faciles à éviter)
        if toll.get('role') == 'O':  # Péage ouvert
            priority += 5
        
        # 4. Gestionnaire (certains sont plus faciles à éviter que d'autres)
        gestionnaire = toll.get('gestionnaire', '').upper()
        if gestionnaire == 'APRR':
            priority += 2  # Les péages APRR ont souvent des alternatives
        
        return priority
