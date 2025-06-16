"""
combination_generator.py
-----------------------

Responsabilité : Générer les combinaisons de péages à tester.
Priorise les combinaisons par coût estimé (moins cher en premier).
"""

from src.services.toll.constants import TollOptimizationConfig as Config
from src.services.toll_cost import add_marginal_cost
from itertools import combinations


class CombinationGenerator:
    """
    Générateur de combinaisons de péages optimisé.
    Responsabilité unique : créer et prioriser les combinaisons à tester.
    """
    
    def __init__(self):
        pass
    
    def generate_combinations(self, departure, arrival, available_tolls, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Génère les combinaisons de péages triées par coût estimé.
        
        Args:
            departure: Coordonnées de départ [lon, lat]
            arrival: Coordonnées d'arrivée [lon, lat]  
            available_tolls: Liste des péages disponibles sur/proche de la route
            max_tolls: Nombre maximum de péages autorisés
            veh_class: Classe de véhicule pour calcul du coût
            
        Returns:            list: Combinaisons triées par coût croissant
                 Format: [{'waypoints': [départ, péage1, péage2, arrivée], 'estimated_cost': float}]
        """
        print(f"🎯 Génération des combinaisons avec exactement {max_tolls} péages")
        
        if max_tolls == 0:
            # Cas spécial : route directe sans péages
            return [{'waypoints': [departure, arrival], 'estimated_cost': 0.0, 'toll_count': 0, 'tolls': []}]
        
        combinations_list = []
        
        # Générer SEULEMENT les combinaisons avec exactement max_tolls péages
        if max_tolls <= len(available_tolls):
            for toll_combination in combinations(available_tolls, max_tolls):
                # Créer les waypoints : départ + péages + arrivée
                waypoints = [departure] + list(toll_combination) + [arrival]
                
                # Estimer le coût de cette combinaison
                estimated_cost = self._estimate_combination_cost(toll_combination, veh_class)
                
                combinations_list.append({
                    'waypoints': waypoints,
                    'estimated_cost': estimated_cost,
                    'toll_count': max_tolls,
                    'tolls': list(toll_combination)  # Ajouter la liste des péages
                })
        else:
            print(f"⚠️ Impossible de générer des combinaisons avec {max_tolls} péages (seulement {len(available_tolls)} disponibles)")        # Trier par coût croissant (moins cher en premier)
        combinations_list.sort(key=lambda x: x['estimated_cost'])
        
        print(f"✅ {len(combinations_list)} combinaisons générées et triées par coût")
        return combinations_list

    def _estimate_combination_cost(self, toll_combination, veh_class):
        """
        Estime le coût total d'une combinaison de péages.
        
        NOUVELLE LOGIQUE :
        - Péages ouverts (APRR_O) : coût fixe individuel
        - Péages fermés (APRR_F) : coût basé sur les segments entre entrée/sortie
        - Combinaisons : somme des coûts de chaque segment identifié
        
        Args:
            toll_combination: Tuple de péages
            veh_class: Classe de véhicule            
        Returns:
            float: Coût estimé total
        """
        total_cost = 0.0
        print(f"    💰 Calcul coût pour {len(toll_combination)} péages...")
        
        # Récupérer les données de coût
        from src.services.toll_data_cache import toll_data_cache
        edges_df = toll_data_cache.virtual_edges_df
        
        # Séparer péages ouverts et fermés
        open_tolls = []  # APRR_O
        closed_tolls = []  # APRR_F
        
        for i, toll in enumerate(toll_combination):
            if not isinstance(toll, dict):
                print(f"⚠️ Péage {i} n'est pas un dictionnaire: {type(toll)} = {toll}")
                total_cost += 2.0  # Coût moyen estimé
                continue
            
            toll_id = toll.get('id', 'N/A')
            print(f"    🔍 Péage {i+1}/{len(toll_combination)}: ID={toll_id}")
            
            if toll_id.startswith("APRR_O"):
                open_tolls.append((toll_id, toll))
            elif toll_id.startswith("APRR_F"):
                closed_tolls.append((toll_id, toll))
        
        # Calculer coûts des péages ouverts (coût fixe)
        for toll_id, toll in open_tolls:
            try:
                cost = edges_df.loc[(toll_id, toll_id)][veh_class]
                print(f"    💰 Péage ouvert {toll_id}: {cost}€")
                total_cost += cost
            except KeyError:
                print(f"    ⚠️ Coût péage ouvert {toll_id} non trouvé, fallback 2.0€")
                total_cost += 2.0
        
        # Calculer coûts des péages fermés (segments)
        if len(closed_tolls) >= 2:
            # Si on a plusieurs péages fermés, calculer le coût du segment global
            # Prendre le premier comme entrée et le dernier comme sortie
            # TODO: Améliorer cette logique si nécessaire
            entry_id = closed_tolls[0][0]
            exit_id = closed_tolls[-1][0]
            
            try:
                segment_cost = edges_df.loc[(entry_id, exit_id)][veh_class]
                print(f"    💰 Segment fermé {entry_id} → {exit_id}: {segment_cost}€")
                total_cost += segment_cost
            except KeyError:
                # Si le segment direct n'existe pas, calculer somme des segments intermédiaires
                segment_cost = 0.0
                for i in range(len(closed_tolls) - 1):
                    from_id = closed_tolls[i][0]
                    to_id = closed_tolls[i + 1][0]
                    try:
                        step_cost = edges_df.loc[(from_id, to_id)][veh_class]
                        segment_cost += step_cost
                        print(f"    💰 Étape {from_id} → {to_id}: {step_cost}€")
                    except KeyError:
                        print(f"    ⚠️ Segment {from_id} → {to_id} non trouvé, fallback 1.0€")
                        segment_cost += 1.0
                
                if segment_cost > 0:
                    total_cost += segment_cost
                    print(f"    💰 Total segments fermés: {segment_cost}€")
                else:
                    print(f"    ⚠️ Aucun segment fermé trouvé, fallback {len(closed_tolls) * 1.5}€")
                    total_cost += len(closed_tolls) * 1.5
        
        elif len(closed_tolls) == 1:
            # Un seul péage fermé, considérer comme coût moyen
            toll_id = closed_tolls[0][0]
            print(f"    💰 Péage fermé unique {toll_id}: 2.5€ (estimation)")
            total_cost += 2.5
        
        print(f"    💰 Coût total estimé: {total_cost:.2f}€")
        return total_cost

    def generate_valid_combinations(self, departure, arrival, available_tolls, max_tolls, veh_class=Config.DEFAULT_VEH_CLASS):
        """
        Génère des combinaisons VALIDES de péages selon la logique métier française.
        
        RÈGLES MÉTIER :
        - Péage ouvert (APRR_O) : Prix fixe, peut être seul
        - Péages fermés (APRR_F) : Fonctionnent par paires entrée/sortie
        - Combinaisons valides :
          * [APRR_O] (péage ouvert seul)
          * [APRR_F_entrée, APRR_F_sortie] (segment fermé)
          * [APRR_O, APRR_F_entrée, APRR_F_sortie] (ouvert + segment)
          * Plusieurs péages ouverts + segments fermés
        
        Args:
            departure: Coordonnées de départ [lon, lat]
            arrival: Coordonnées d'arrivée [lon, lat]  
            available_tolls: Liste des péages disponibles
            max_tolls: Nombre maximum de péages par combinaison
            veh_class: Classe de véhicule pour estimation du coût
            
        Returns:
            list: Combinaisons valides triées par coût croissant
        """
        print(f"🎯 Génération de combinaisons VALIDES avec exactement {max_tolls} péages")
        
        if max_tolls == 0:
            return [{'waypoints': [departure, arrival], 'estimated_cost': 0.0, 'toll_count': 0, 'tolls': []}]
        
        # Séparer péages ouverts et fermés
        open_tolls = []
        closed_tolls = []
        
        for toll in available_tolls:
            toll_id = toll.get('id', '') if isinstance(toll, dict) else str(toll)
            if toll_id.startswith('APRR_O'):
                open_tolls.append(toll)
            elif toll_id.startswith('APRR_F'):
                closed_tolls.append(toll)
        
        print(f"🔍 Péages disponibles: {len(open_tolls)} ouverts, {len(closed_tolls)} fermés")
        
        valid_combinations = []
        
        # === 1. COMBINAISONS PÉAGES OUVERTS SEULS ===
        if max_tolls <= len(open_tolls):
            for open_combo in combinations(open_tolls, max_tolls):
                waypoints = [departure] + list(open_combo) + [arrival]
                cost = self._estimate_valid_combination_cost(open_combo, veh_class)
                valid_combinations.append({
                    'waypoints': waypoints,
                    'estimated_cost': cost,
                    'toll_count': max_tolls,
                    'tolls': list(open_combo),
                    'type': 'open_only'
                })
        
        # === 2. COMBINAISONS SEGMENTS FERMÉS SEULS ===
        if max_tolls >= 2 and max_tolls % 2 == 0 and len(closed_tolls) >= max_tolls:
            for closed_combo in combinations(closed_tolls, max_tolls):
                waypoints = [departure] + list(closed_combo) + [arrival]
                cost = self._estimate_valid_combination_cost(closed_combo, veh_class)
                valid_combinations.append({
                    'waypoints': waypoints,
                    'estimated_cost': cost,
                    'toll_count': max_tolls,
                    'tolls': list(closed_combo),
                    'type': 'closed_segments'
                })
        
        # === 3. COMBINAISONS MIXTES (OUVERTS + SEGMENTS FERMÉS) ===
        for num_open in range(1, min(len(open_tolls) + 1, max_tolls)):
            remaining_slots = max_tolls - num_open
            if remaining_slots >= 2 and remaining_slots % 2 == 0 and len(closed_tolls) >= remaining_slots:
                for open_combo in combinations(open_tolls, num_open):
                    for closed_combo in combinations(closed_tolls, remaining_slots):
                        mixed_combo = list(open_combo) + list(closed_combo)
                        waypoints = [departure] + mixed_combo + [arrival]
                        cost = self._estimate_valid_combination_cost(tuple(mixed_combo), veh_class)
                        valid_combinations.append({
                            'waypoints': waypoints,
                            'estimated_cost': cost,
                            'toll_count': max_tolls,
                            'tolls': mixed_combo,
                            'type': 'mixed'
                        })
        
        # Trier par coût croissant
        valid_combinations.sort(key=lambda x: x['estimated_cost'])
        
        print(f"✅ {len(valid_combinations)} combinaisons VALIDES générées et triées par coût")
        return valid_combinations
    
    def _estimate_valid_combination_cost(self, toll_combination, veh_class):
        """
        Estime le coût d'une combinaison VALIDE en utilisant la logique métier correcte.
        Utilise la fonction add_marginal_cost qui respecte les règles des péages.
        
        Args:
            toll_combination: Tuple de péages
            veh_class: Classe de véhicule            
        Returns:
            float: Coût estimé total
        """
        if not toll_combination:
            return 0.0
        
        print(f"    💰 Calcul coût VALIDE pour {len(toll_combination)} péages...")
        
        # Convertir en liste de dictionnaires pour add_marginal_cost
        tolls_list = []
        for toll in toll_combination:
            if isinstance(toll, dict):
                tolls_list.append(toll.copy())
            else:
                print(f"⚠️ Péage invalide ignoré: {toll}")
                continue
        
        if not tolls_list:
            return 0.0
        
        try:
            # Utiliser la logique métier officielle
            from src.services.toll_cost import add_marginal_cost
            tolls_with_cost = add_marginal_cost(tolls_list, veh_class)
            total_cost = sum(t.get('cost', 0) for t in tolls_with_cost)
            
            print(f"    💰 Coût total VALIDE: {total_cost:.2f}€")
            return total_cost
            
        except Exception as e:
            print(f"⚠️ Erreur calcul coût valide: {e}")
            # Fallback vers l'ancienne méthode si erreur
            return self._estimate_combination_cost(toll_combination, veh_class)
