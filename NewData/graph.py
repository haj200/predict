import matplotlib.pyplot as plt
import numpy as np

# Vos données
data = {
    "Fournitures et pièces de rechange pour matériel technique et informatique": {
        "total": 63, "correct": 9, "accuracy": 14.29
    },
    "Achat de matériel technique, de logiciels et de matériel informatique": {
        "total": 193, "correct": 18, "accuracy": 9.33
    },
    "Achat de matériel audiovisuel, sonore et de mise en lumière": {
        "total": 20, "correct": 2, "accuracy": 10.0
    },
    "Achat de matériels et articles de sport, de literie, de linge, de couchage, de cuisine et de buanderie": {
        "total": 45, "correct": 5, "accuracy": 11.11
    },
    "Achat de matériel de transport, de citernes et d’engins": {
        "total": 22, "correct": 2, "accuracy": 9.09
    },
    "Prestations d’impression, de tirage, de reproduction et de photographie": {
        "total": 65, "correct": 7, "accuracy": 10.77
    },
    "Achat de cartables, de livres, de manuels, et de fournitures scolaires et de matériel d’enseignement": {
        "total": 25, "correct": 3, "accuracy": 12.0
    },
    "Fourniture d’engrais, de graines, de plantes, de plants et de portoirs": {
        "total": 5, "correct": 1, "accuracy": 20.0
    },
    "Achat de matériel d’éclairage public": {
        "total": 40, "correct": 9, "accuracy": 22.5
    },
    "Achat de produits pharmaceutiques non-médicamenteux, de gaz médicaux et de réactifs de laboratoires": {
        "total": 23, "correct": 3, "accuracy": 13.04
    },
    "Organisation de manifestations culturelles, scientifiques et sportives": {
        "total": 23, "correct": 7, "accuracy": 30.43
    },
    "Entretien et réparation de matériel technique, de mobilier et des installations techniques": {
        "total": 61, "correct": 16, "accuracy": 26.23
    },
    "Prestations médicales, hospitalières, radiologiques, d’analyse médicale et de brancardage": {
        "total": 3, "correct": 1, "accuracy": 33.33
    },
    "Travaux de branchement et d’extension du réseau d’eau potable et d’électricité": {
        "total": 17, "correct": 2, "accuracy": 11.76
    },
    "Travaux d’aménagement des espaces verts avec ou sans fourniture de graines et plantes": {
        "total": 11, "correct": 3, "accuracy": 27.27
    },
    "Achat de fournitures de bureau et de documentation": {
        "total": 136, "correct": 28, "accuracy": 20.59
    },
    "Location d’engins et de moyens de transport de matériels et matériaux et d’engins": {
        "total": 17, "correct": 4, "accuracy": 23.53
    },
    "Études, conseil et formation": {
        "total": 109, "correct": 17, "accuracy": 15.6
    },
    "Achat de pièces de rechange et pneumatiques pour véhicules et engins": {
        "total": 17, "correct": 2, "accuracy": 11.76
    },
    "Achat de produits chimiques et de laboratoire, pesticides et insecticides": {
        "total": 29, "correct": 4, "accuracy": 13.79
    },
    "Achat de produits d’impression, de reproduction et de photographie": {
        "total": 23, "correct": 10, "accuracy": 43.48
    },
    "Achat de matériel électrique, de groupes électrogènes, d’électropompes et de motopompes de chantier": {
        "total": 26, "correct": 4, "accuracy": 15.38
    },
    "Prestations d’hôtellerie, d’hébergement, de réception et de restauration": {
        "total": 174, "correct": 30, "accuracy": 17.24
    },
    "Prestation de jardinage, de gardiennage et de nettoyage": {
        "total": 36, "correct": 9, "accuracy": 25.0
    },
    "Location de matériel et de mobilier": {
        "total": 8, "correct": 1, "accuracy": 12.5
    },
    "Achat d’habillement": {
        "total": 25, "correct": 8, "accuracy": 32.0
    },
    "Achat de matières premières pour le textile, le cuir, la reliure des documents et autres": {
        "total": 5, "correct": 1, "accuracy": 20.0
    },
    "Prestations de remise en état et de recharge des extincteurs": {
        "total": 21, "correct": 0, "accuracy": 0.0
    },
    "Travaux d’équipement et de renforcement des postes MT/BT du réseau d’électricité": {
        "total": 3, "correct": 0, "accuracy": 0.0
    },
    "Achat de matériaux de construction": {
        "total": 67, "correct": 10, "accuracy": 14.93
    },
    "Prestations géotechniques et de laboratoire": {
        "total": 14, "correct": 4, "accuracy": 28.57
    },
    "Achat de pièces de rechange pour matériel technique et informatique": {
        "total": 20, "correct": 3, "accuracy": 15.0
    },
    "Achat de papeteries et d’imprimés": {
        "total": 24, "correct": 6, "accuracy": 25.0
    },
    "Contrôle et expertise techniques": {
        "total": 11, "correct": 3, "accuracy": 27.27
    },
    "Fourniture de verrerie, petit matériel et outillage de laboratoire": {
        "total": 16, "correct": 3, "accuracy": 18.75
    },
    "Achat de produits alimentaires pour usage humain": {
        "total": 41, "correct": 7, "accuracy": 17.07
    },
    "Travaux d’installation de matériels divers": {
        "total": 33, "correct": 3, "accuracy": 9.09
    },
    "Achat de médicaments": {
        "total": 14, "correct": 1, "accuracy": 7.14
    },
    "Achat de matériel de sécurité et de lutte contre l’incendie": {
        "total": 12, "correct": 1, "accuracy": 8.33
    },
    "Achat d’affiches et d’articles publicitaires": {
        "total": 5, "correct": 0, "accuracy": 0.0
    },
    "Achat de badges, de médailles, d’effigies, de fanions, de drapeaux et de portraits": {
        "total": 70, "correct": 18, "accuracy": 25.71
    },
    "Achat de carburants et de lubrifiants": {
        "total": 22, "correct": 4, "accuracy": 18.18
    },
    "Fourniture de films et de produits radiologiques": {
        "total": 6, "correct": 0, "accuracy": 0.0
    },
    "Location de moyens de transport des personnes (voitures et autocars)": {
        "total": 13, "correct": 3, "accuracy": 23.08
    },
    "Achat d’articles de droguerie, de quincaillerie, d’électricité, de menuiserie et de plomberie sanitaire": {
        "total": 102, "correct": 21, "accuracy": 20.59
    },
    "Travaux d’aménagement, d’entretien et de réparation des ouvrages, voies et réseaux": {
        "total": 39, "correct": 10, "accuracy": 25.64
    },
    "Fourniture de fongibles médicaux et de fils chirurgicaux": {
        "total": 10, "correct": 1, "accuracy": 10.0
    },
    "Fourniture de combustibles et de produits de chauffage": {
        "total": 6, "correct": 4, "accuracy": 66.67
    },
    "Achat de matériel, de câbles, coffrets de distribution, de poteaux et autres accessoires de branchements moyenne tension et basse tension": {
        "total": 3, "correct": 0, "accuracy": 0.0
    },
    "Fourniture d’équipements médico-techniques et de pièces de rechange y afférentes": {
        "total": 15, "correct": 1, "accuracy": 6.67
    },
    "Achat de matériel de diagnostic, de recherche, de détection, de signalisation de défaut et de matériel de mesure": {
        "total": 11, "correct": 1, "accuracy": 9.09
    },
    "Achat de produits alimentaires pour usage animal": {
        "total": 5, "correct": 2, "accuracy": 40.0
    },
    "Fournitures pour le traitement et la conservation préventive des archives": {
        "total": 1, "correct": 0, "accuracy": 0.0
    },
    "Achat de mobilier, d’enseignement, de laboratoire et d’exposition": {
        "total": 5, "correct": 0, "accuracy": 0.0
    },
    "Achat de matériel et d’équipement de plongée sous-marine": {
        "total": 2, "correct": 1, "accuracy": 50.0
    },
    "Prestations topographiques et océanographiques": {
        "total": 32, "correct": 4, "accuracy": 12.5
    },
    "Entretien et maintenance des équipements informatique": {
        "total": 8, "correct": 1, "accuracy": 12.5
    },
    "Achat de pièces de rechange pour les équipements médicotechniques": {
        "total": 5, "correct": 0, "accuracy": 0.0
    },
    "Achat de produits pour traitement d’eau potable": {
        "total": 3, "correct": 0, "accuracy": 0.0
    },
    "Location de salles, de stands et de mobilier d’exposition": {
        "total": 11, "correct": 1, "accuracy": 9.09
    },
    "Entretien et maintenance de logiciels et de progiciels": {
        "total": 3, "correct": 2, "accuracy": 66.67
    },
    "Transport, acconage, magasinage et transit": {
        "total": 13, "correct": 0, "accuracy": 0.0
    },
    "Prestations d’assistance et de conseil technique, juridique et comptable": {
        "total": 8, "correct": 2, "accuracy": 25.0
    },
    "Achat de produits vétérinaires et de produits d’élevage aquacole": {
        "total": 1, "correct": 0, "accuracy": 0.0
    },
    "Prestations de publicité, de sensibilisation et supports multimédia": {
        "total": 4, "correct": 1, "accuracy": 25.0
    },
    "Fourniture de sacs et produits d’emballage": {
        "total": 6, "correct": 1, "accuracy": 16.67
    },
    "Fournitures et produits d’entretien et de nettoyage": {
        "total": 63, "correct": 9, "accuracy": 14.29
    },
    "Prestations de désinsectisation, de dératisation et prestations de lutte contre les animaux errants": {
        "total": 1, "correct": 0, "accuracy": 0.0
    },
    "Achat de matières premières pour laboratoire et enseignement": {
        "total": 4, "correct": 0, "accuracy": 0.0
    },
    "Achat d’articles de correction de la vue et articles pour personnes à besoins spécifiques": {
        "total": 3, "correct": 1, "accuracy": 33.33
    },
    "Prestations d’entretien des véhicules et engins": {
        "total": 4, "correct": 1, "accuracy": 25.0
    },
    "Prestations de contrôle des points de comptage": {
        "total": 1, "correct": 1, "accuracy": 100.0
    },
    "Direction, animation et participation des artistes, intellectuels, conférenciers et techniciens aux manifestations et activités culturelles": {
        "total": 1, "correct": 0, "accuracy": 0.0
    },
    "Travaux d’aménagement, d’entretien et de réparation des logements militaires": {
        "total": 1, "correct": 0, "accuracy": 0.0
    },
    "Prestations de contrôle et d’analyse des échantillons prélevés sur les produits, matériel et matériaux soumis à des normes obligatoires": {
        "total": 2, "correct": 0, "accuracy": 0.0
    },
    "Travaux d’aménagement et d’entretien des installations militaires": {
        "total": 2, "correct": 0, "accuracy": 0.0
    },
    "Fournitures pour inauguration et pose de premières pierres": {
        "total": 2, "correct": 0, "accuracy": 0.0
    },
    "Travaux d’aménagement, d’entretien et de réparation des bâtiments administratifs": {
        "total": 172, "correct": 22, "accuracy": 12.79
    },
    "Travaux de raccordement au réseau d’assainissement et de curage": {
        "total": 2, "correct": 0, "accuracy": 0.0
    },
    "Location de camions citernes": {
        "total": 2, "correct": 0, "accuracy": 0.0
    },
    "Achat d’animaux": {
        "total": 1, "correct": 0, "accuracy": 0.0
    },
    "Fourniture de l’instrumentation médicotechnique": {
        "total": 3, "correct": 1, "accuracy": 33.33
    },
    "Prestations de collecte, de traitement et de blanchissage du linge": {
        "total": 1, "correct": 0, "accuracy": 0.0
    },
    "Achat de matériel et de mobilier de bureau": {
        "total": 79, "correct": 12, "accuracy": 15.19
    }
}

# Extraire les données et les trier globalement une fois pour garder la cohérence
all_items = []
for category, values in data.items():
    all_items.append((category, values["accuracy"], values["total"]))

# Trier toutes les catégories par accuracy décroissante
all_items_sorted = sorted(all_items, key=lambda x: x[1], reverse=True)

# Définir la taille des groupes
group_size = 20

# Définir les couleurs
bar_color = '#4CAF50' # Un vert agréable pour les barres
background_color = '#fffcfa' # Votre couleur pour le fond

# Créer les graphiques par groupes
for i in range(0, len(all_items_sorted), group_size):
    current_group = all_items_sorted[i:i + group_size]
    
    group_categories = [item[0] for item in current_group]
    group_accuracies = [item[1] for item in current_group]
    group_totals = [item[2] for item in current_group]

    fig, ax = plt.subplots(figsize=(14, 10)) # Taille de la figure
    fig.patch.set_facecolor(background_color) # Définir la couleur de fond de la figure
    ax.set_facecolor(background_color) # Définir la couleur de fond de l'axe

    y_pos = np.arange(len(group_categories))
    
    # Créer les barres horizontales
    bars = ax.barh(y_pos, group_accuracies, color=bar_color, height=0.7)

    # Ajouter les valeurs d'accuracy et le total sur les barres
    for idx, (accuracy_val, total_val) in enumerate(zip(group_accuracies, group_totals)):
        ax.text(accuracy_val + 1, y_pos[idx], f'{accuracy_val:.2f}% ({total_val})', 
                va='center', ha='left', color='black', fontsize=9)

    # Labels et titre
    ax.set_yticks(y_pos)
    ax.set_yticklabels(group_categories, fontsize=10) # Taille de police pour les labels y
    ax.set_xlabel("Précision (%)", fontsize=12, color='black')
    
    start_idx = i + 1
    end_idx = min(i + group_size, len(all_items_sorted))
    ax.set_title(f"Précision du modèle par nature de l'offre (Catégories {start_idx}-{end_idx})", 
                 fontsize=14, color='black')
    
    ax.set_xlim(0, 100) # L'accuracy est un pourcentage, de 0 à 100%
    ax.invert_yaxis() # Inverser l'axe y pour que la plus haute précision soit en haut

    # Personnalisation des ticks et des bordures
    ax.tick_params(axis='x', colors='black')
    ax.tick_params(axis='y', colors='black')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('black')
    ax.spines['bottom'].set_color('black')
    
    plt.tight_layout() # Ajuster la mise en page
    plt.show() # Afficher le graphique