"""
Toll Association Service
-----------------------

Service pour associer les péages aux liens motorway complets.
"""

from typing import List, Optional, Dict, Any, Tuple
import math

from ..models.complete_motorway_link import CompleteMotorwayLink
from ..models.toll_booth_station import TollBoothStation
from ..linking.coordinate_matcher import calculate_distance_meters


class TollAssociationService:
    """Service pour associer les péages aux liens motorway complets."""
    
    def __init__(self, max_distance_m: float = 2.0):
        """
        Initialise le service d'association.
        
        Args:
            max_distance_m: Distance maximale pour associer un péage à un lien
        """
        self.max_distance_m = max_distance_m
    
    def associate_tolls_to_links(
        self,
        complete_links: List[CompleteMotorwayLink],
        toll_booths: List[TollBoothStation]
    ) -> Dict[str, Any]:
        """
        Associe les péages aux liens motorway complets.
        
        Args:
            complete_links: Liste des liens complets
            toll_booths: Liste des péages
            
        Returns:
            Dict avec les statistiques d'association
        """
        print(f"🏪 Association des péages aux liens motorway...")
        print(f"   • Liens à traiter: {len(complete_links)}")
        print(f"   • Péages disponibles: {len(toll_booths)}")
        print(f"   • Distance max: {self.max_distance_m}m")
        
        stats = {
            "total_links": len(complete_links),
            "total_tolls": len(toll_booths),
            "links_with_tolls": 0,
            "associations_made": 0,
            "average_distance": 0.0,
            "distances": []
        }
        
        for link in complete_links:
            # Chercher des péages proches de ce lien
            associated_tolls = self._find_tolls_near_link(link, toll_booths)
            
            if associated_tolls:
                # Prendre le péage le plus proche
                closest_toll, distance = min(associated_tolls, key=lambda x: x[1])
                
                # Associer le péage au lien
                link.associated_toll = closest_toll
                link.toll_distance_meters = distance
                
                stats["links_with_tolls"] += 1
                stats["associations_made"] += 1
                stats["distances"].append(distance)
        
        # Calculer la distance moyenne
        if stats["distances"]:
            stats["average_distance"] = sum(stats["distances"]) / len(stats["distances"])
        
        self._print_association_stats(stats)
        return stats
    
    def _find_tolls_near_link(
        self,
        link: CompleteMotorwayLink,
        toll_booths: List[TollBoothStation]
    ) -> List[Tuple[TollBoothStation, float]]:
        """
        Trouve les péages proches d'un lien motorway.
        
        Args:
            link: Lien motorway complet
            toll_booths: Liste des péages
            
        Returns:
            List[Tuple[péage, distance]]: Péages trouvés avec leur distance
        """
        nearby_tolls = []
        
        # Récupérer toutes les coordonnées du lien
        link_coordinates = link.get_all_coordinates()
        
        for toll in toll_booths:
            toll_coords = toll.coordinates
            
            # Calculer la distance minimale entre le péage et toutes les coordonnées du lien
            min_distance = float('inf')
            
            for link_coord in link_coordinates:
                distance = calculate_distance_meters(link_coord, toll_coords)
                min_distance = min(min_distance, distance)
            
            # Si la distance est acceptable, ajouter à la liste
            if min_distance <= self.max_distance_m:
                nearby_tolls.append((toll, min_distance))
        
        return nearby_tolls
    
    def _print_association_stats(self, stats: Dict[str, Any]):
        """Affiche les statistiques d'association."""
        print(f"\n📊 Résultats de l'association des péages:")
        print(f"   • Liens traités: {stats['total_links']}")
        print(f"   • Liens avec péages: {stats['links_with_tolls']}")
        print(f"   • Associations créées: {stats['associations_made']}")
        
        if stats['associations_made'] > 0:
            percentage = (stats['links_with_tolls'] / stats['total_links']) * 100
            print(f"   • Pourcentage de liens avec péages: {percentage:.1f}%")
            print(f"   • Distance moyenne: {stats['average_distance']:.2f}m")
            
            # Distribution des distances
            distances = stats['distances']
            if distances:
                print(f"   • Distance min: {min(distances):.2f}m")
                print(f"   • Distance max: {max(distances):.2f}m")
        
        print("✅ Association des péages terminée!\n")
    
    def get_links_with_tolls(self, complete_links: List[CompleteMotorwayLink]) -> List[CompleteMotorwayLink]:
        """Retourne uniquement les liens qui ont des péages associés."""
        return [link for link in complete_links if link.has_toll()]
    
    def get_links_by_toll_type(
        self,
        complete_links: List[CompleteMotorwayLink],
        toll_type: str
    ) -> List[CompleteMotorwayLink]:
        """
        Retourne les liens filtrés par type de péage.
        
        Args:
            complete_links: Liste des liens
            toll_type: "O" pour ouvert, "F" pour fermé
            
        Returns:
            Liste des liens correspondants
        """
        return [
            link for link in complete_links
            if link.has_toll() and link.associated_toll.type == toll_type
        ]
    
    def get_links_by_operator(
        self,
        complete_links: List[CompleteMotorwayLink],
        operator: str
    ) -> List[CompleteMotorwayLink]:
        """
        Retourne les liens filtrés par opérateur de péage.
        
        Args:
            complete_links: Liste des liens
            operator: Nom de l'opérateur (ex: "ASF", "APRR")
            
        Returns:
            Liste des liens correspondants
        """
        return [
            link for link in complete_links
            if link.has_toll() and link.associated_toll.operator == operator
        ]
    
    def generate_toll_association_report(
        self,
        complete_links: List[CompleteMotorwayLink]
    ) -> Dict[str, Any]:
        """
        Génère un rapport détaillé sur les associations de péages.
        
        Args:
            complete_links: Liste des liens complets
            
        Returns:
            Dict avec le rapport détaillé
        """
        links_with_tolls = self.get_links_with_tolls(complete_links)
        
        # Statistiques par type de péage
        open_tolls = self.get_links_by_toll_type(complete_links, "O")
        closed_tolls = self.get_links_by_toll_type(complete_links, "F")
        
        # Statistiques par opérateur
        operators_count = {}
        for link in links_with_tolls:
            operator = link.associated_toll.operator
            operators_count[operator] = operators_count.get(operator, 0) + 1
        
        # Statistiques par type de lien
        entry_links_with_tolls = [
            link for link in links_with_tolls
            if link.link_type.value == "entry"
        ]
        exit_links_with_tolls = [
            link for link in links_with_tolls
            if link.link_type.value == "exit"
        ]
        
        report = {
            "total_links": len(complete_links),
            "links_with_tolls": len(links_with_tolls),
            "coverage_percentage": (len(links_with_tolls) / len(complete_links)) * 100 if complete_links else 0,
            "toll_types": {
                "open_tolls": len(open_tolls),
                "closed_tolls": len(closed_tolls)
            },
            "link_types": {
                "entry_links_with_tolls": len(entry_links_with_tolls),
                "exit_links_with_tolls": len(exit_links_with_tolls)
            },
            "operators": operators_count,
            "distance_stats": {
                "distances": [link.toll_distance_meters for link in links_with_tolls if link.toll_distance_meters is not None],
            }
        }
        
        # Calculer les statistiques de distance
        distances = report["distance_stats"]["distances"]
        if distances:
            report["distance_stats"].update({
                "min_distance": min(distances),
                "max_distance": max(distances),
                "average_distance": sum(distances) / len(distances),
                "count": len(distances)
            })
        
        return report
    
    def print_toll_association_report(self, complete_links: List[CompleteMotorwayLink]):
        """Affiche un rapport détaillé sur les associations de péages."""
        report = self.generate_toll_association_report(complete_links)
        
        print(f"\n📋 RAPPORT D'ASSOCIATION DES PÉAGES")
        print(f"{'=' * 40}")
        print(f"📊 Vue d'ensemble:")
        print(f"   • Total liens: {report['total_links']}")
        print(f"   • Liens avec péages: {report['links_with_tolls']}")
        print(f"   • Couverture: {report['coverage_percentage']:.1f}%")
        
        print(f"\n🏪 Types de péages:")
        print(f"   • Péages ouverts: {report['toll_types']['open_tolls']}")
        print(f"   • Péages fermés: {report['toll_types']['closed_tolls']}")
        
        print(f"\n🛣️  Types de liens:")
        print(f"   • Entrées avec péages: {report['link_types']['entry_links_with_tolls']}")
        print(f"   • Sorties avec péages: {report['link_types']['exit_links_with_tolls']}")
        
        print(f"\n🏢 Opérateurs (top 10):")
        sorted_operators = sorted(report['operators'].items(), key=lambda x: x[1], reverse=True)
        for operator, count in sorted_operators[:10]:
            print(f"   • {operator}: {count} liens")
        
        if report['distance_stats'].get('count', 0) > 0:
            dist_stats = report['distance_stats']
            print(f"\n📏 Distances d'association:")
            print(f"   • Moyenne: {dist_stats['average_distance']:.2f}m")
            print(f"   • Min: {dist_stats['min_distance']:.2f}m")
            print(f"   • Max: {dist_stats['max_distance']:.2f}m")
            print(f"   • Total mesures: {dist_stats['count']}")
        
        print(f"\n✅ Rapport d'association terminé!\n")
