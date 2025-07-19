import pandas as pd
from datetime import datetime

def export_to_excel(results, output_dir="output"):
    data = []

    # Parcourir les catégories
    for categorie, films in results["categories"].items():
        for film in films:
            for cinema, info in film["cinemas"].items():
                for seance in info["seances"]:
                    row = {
                        "Catégorie": categorie,
                        "Film": film["titre"],
                        "Genre": film.get("genre", ""),
                        "Label": film.get("label", ""),
                        "Cinéma": cinema,
                        "Adresse": info["adresse"],
                        "Date": seance["date"],
                        "Heure": seance["heure_debut"],
                        "Version": seance["version"],
                        "Salle": seance["salle"],
                        "URL": film["url"]
                    }
                    data.append(row)

    # Créer les DataFrames triés
    df_by_type = pd.DataFrame(data).sort_values(by=["Catégorie", "Film", "Cinéma", "Date", "Heure"])
    df_by_film = pd.DataFrame(data).sort_values(by=["Film", "Cinéma", "Date", "Heure"])

    # Nom du fichier
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_file = f'{output_dir}/ugc_films_seances_{timestamp}.xlsx'

    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df_by_type.to_excel(writer, sheet_name='Par catégorie', index=False)
        df_by_film.to_excel(writer, sheet_name='Par film', index=False)

        workbook = writer.book
        formats = {
            "header": workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'top',
                'bg_color': '#D9E1F2', 'border': 1
            }),
            "cell": workbook.add_format({
                'text_wrap': True, 'valign': 'top', 'border': 1
            })
        }

        for sheet_name in ['Par catégorie', 'Par film']:
            worksheet = writer.sheets[sheet_name]

            for col_num, value in enumerate(df_by_type.columns.values):
                worksheet.write(0, col_num, value, formats["header"])

            worksheet.set_column('A:A', 15)
            worksheet.set_column('B:B', 30)
            worksheet.set_column('C:C', 15)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 25)
            worksheet.set_column('F:F', 35)
            worksheet.set_column('G:G', 12)
            worksheet.set_column('H:H', 10)
            worksheet.set_column('I:I', 10)
            worksheet.set_column('J:J', 10)
            worksheet.set_column('K:K', 50)

            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(0, 0, len(data), len(df_by_type.columns) - 1)

    print(f"\nLes informations ont été exportées dans {excel_file}")
    return excel_file 