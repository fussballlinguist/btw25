import streamlit as st
import pandas as pd
import plotly.express as px
import random
from datetime import datetime
from collections import Counter
import numpy as np

today_date = datetime.today().strftime("%d.%m.%Y")

st.write("### Abfrage zu Worthäufigkeiten in Wahlprogrammen (Beta)")
st.write(f"Ein Tool von [Simon Meier-Vieracker](https://tu-dresden.de/gsw/slk/germanistik/al/die-professur/inhaber), Stand {today_date}")

programs = {
    "AfD": "https://www.afd.de/wp-content/uploads/2025/02/AfD_Bundestagswahlprogramm2025_web.pdf",
    "BSW": "https://bsw-vg.de/wp-content/themes/bsw/assets/downloads/BSW%20Wahlprogramm%202025.pdf",
    "CDU": "https://www.cdu.de/app/uploads/2025/01/km_btw_2025_wahlprogramm_langfassung_ansicht.pdf",
    "FDP": "https://www.fdp.de/sites/default/files/2024-12/fdp-wahlprogramm_2025.pdf",
    "Gruene": "https://cms.gruene.de/uploads/assets/20250205_Regierungsprogramm_DIGITAL_DINA5.pdf",
    "Linke": "https://www.die-linke.de/fileadmin/user_upload/Wahlprogramm_Langfassung_Linke-BTW25_01.pdf",
    "SPD": "https://www.spd.de/fileadmin/Dokumente/Beschluesse/Programm/2025_SPD_Regierungsprogramm.pdf"
}

flection = {
    "AfD": "der AfD",
    "BSW": "des BSW",
    "CDU": "der CDU",
    "FDP": "der FDP",
    "Gruene": "der Grünen",
    "Linke": "der Linken",
    "SPD": "der SPD"    
}

# UI for input
lemma = st.text_input("Suchwort eingeben (unflektierte Grundform): ")

# Load data
df = pd.read_csv("btw25_corrected.tsv", sep="\t", quoting=3)

# Group data by lemma and party
df_grouped = df.groupby(['lemma', 'party']).size().reset_index(name='freq')

def generate_kwic(df, query_lemma, selected_party, context_size=15, max_examples=10):
    # Filter the DataFrame for the query lemma and party
    filtered_df = df[(df["lemma"] == query_lemma) & (df["party"] == selected_party)].reset_index()

    # If there are fewer examples than max_examples, adjust the number of examples to the available count
    num_examples_to_select = min(len(filtered_df), max_examples)

    # Randomly sample the rows
    sampled_rows = filtered_df.sample(n=num_examples_to_select)

    kwic_examples = []
    for _, row in sampled_rows.iterrows():
        index = row['index']  # Get the current row index
        start = max(index - context_size, 0)  # Start of the context
        end = min(index + context_size + 1, len(df))  # End of the context

        # Extract tokens and indices for the context
        context_tokens = df.iloc[start:end]["token"].tolist()
        context_indices = df.iloc[start:end].index.tolist()

        # Highlight the query token
        kwic_line = " ".join(
            [f"**{token}**" if idx == index else token for token, idx in zip(context_tokens, context_indices)]
        )
        kwic_examples.append(kwic_line)

    return kwic_examples

def get_collocations(df, query_lemma, selected_party, context_size=5):
    filtered_df = df[(df["lemma"] == query_lemma) & (df["party"] == selected_party)].reset_index()
    df_party = df[df["party"] == selected_party].reset_index()
    collocation_base = []

    for _, row in filtered_df.iterrows():
        index = row['index']  # Get the current row index
        start = max(index - context_size, 0)  # Start of the context
        end = min(index + context_size + 1, len(df))  # End of the context
        context_lemmas = (
            df.iloc[start:index]["lemma"].to_list() +  # Tokens before the current lemma
            df.iloc[index + 1:end]["lemma"].to_list()  # Tokens after the current lemma
        )
        collocation_base.extend(context_lemmas)

    df_collo = pd.DataFrame(Counter(collocation_base).most_common(), columns=["lemma","freq"])
    df_collo["size"] = df_collo["freq"].sum()
    
    df_party_freq = df_party.groupby("lemma").size().reset_index(name='freq_total')
    df_collo = df_collo.merge(df_party_freq, on="lemma")
    
    df_collo["freq_reference"] = df_collo["freq_total"] - df_collo["freq"]
    df_collo["size_reference"] = df_collo["freq_reference"].sum()
    df_collo["relfreq"] = df_collo.freq / df_collo.size
    df_collo["relfreq_reference"] = (df_collo.freq_reference) / df_collo.size_reference
    df_collo.loc[df_collo["relfreq_reference"] == 0, "relfreq_reference"] = 0.5
    df_collo["LogRatio"] = np.log2(df_collo.relfreq / df_collo.relfreq_reference)
    
    return df_collo

if lemma:
    # Filter data for the input lemma
    df_lemma = df_grouped[df_grouped["lemma"] == lemma].reset_index(drop=True)
    df_size = pd.DataFrame(df["party"].value_counts(normalize=False))
    df_size = df_size.rename(columns={"party": "count"})
    df_lemma = pd.merge(df_lemma, df_size, on='party', how='outer')
    df_lemma["relfreq"] = df_lemma["freq"] / df_lemma["count"] * 1000000

    mean = (df_lemma["freq"].sum() / df_lemma["count"].sum() * 1000000)

    # Adjust the relfreq column to center around the mean
    df_lemma['relfreq_centered'] = df_lemma['relfreq'] - mean

    # Define party colors
    party_colors = {
        'AfD': '#00ccff',
        'BSW': '#cc1953',
        'CDU': '#2d3c4b',
        'FDP': '#ffed00',
        'Gruene': '#008939',
        'Linke': '#D675D8',
        'SPD': '#E3000F'
    }

    # Create interactive bar plots using Plotly
    # First variant: Relative frequencies
    fig = px.bar(
        df_lemma,
        x="party",
        y="relfreq",
        color="party",
        color_discrete_map=party_colors,
        labels={"relfreq": "Relative Häufigkeit"},
        title=f"Relative Häufigkeiten von '{lemma}'",
        hover_data={"freq": True, "relfreq": True, "relfreq_centered": False},
        custom_data=["relfreq","freq"]
    )

    fig.update_layout(
        #autosize=True,
        margin={"l": 40, "r": 40, "t": 60, "b": 00},
        title_y=.9,
        showlegend=False,
        xaxis=dict(
           tickangle=-45,
           title=""
        )
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"  # Party name
            "Relative Häufigkeit: %{customdata[0]:.2f}<br>"  # 'relfreq' formatted to 2 decimals
            "Absolute Häufigkeit: %{customdata[1]}"  # 'freq' displayed normally
        )
    )
    
    # Second variant: Mean-centered relative frequencies
    fig2 = px.bar(
        df_lemma,
        x="party",
        y="relfreq_centered",
        color="party",
        color_discrete_map=party_colors,
        labels={"relfreq_centered": "Abweichung der relativen Häufigkeit"},
        title=f"Relative Häufigkeiten von '{lemma}' (mittelwertzentriert)",
        hover_data={"freq": True, "relfreq": True, "relfreq_centered": False},
        custom_data=["relfreq","freq"]
    )

    fig2.update_layout(
        #autosize=True,
        margin={"l": 40, "r": 40, "t": 60, "b": 00},
        title_y=.9,
        showlegend=False,
        xaxis=dict(
           tickangle=-45,
           title=""
        )
    )

    fig2.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"  # Party name
            "Relative Häufigkeit: %{customdata[0]:.2f}<br>"  # 'relfreq' formatted to 2 decimals
            "Absolute Häufigkeit: %{customdata[1]}"  # 'freq' displayed normally
        )
    )

    # Display the interactive plots in two tabs
    tab1, tab2 = st.tabs(["Relative Häufigkeiten", "Relative Häufigkeiten (mittelwertzentriert)"])
    with tab1:
        st.plotly_chart(fig, use_container_width=True)     
    with tab2:
        st.plotly_chart(fig2, use_container_width=True)    
    
    # Display the raw data
    df_lemma_display = df_lemma.dropna(subset=["freq"])
    with st.expander("Tabelle anzeigen"):
        st.dataframe(df_lemma_display)    
    
    party_options = list(df_lemma["party"].unique())

    default_party = "Gruene"  # Replace with your preferred default party

    # Capture user interaction
    clicked_party = st.selectbox(
        "Partei auswählen für eine Zufallsauswahl von max. 10 Belegen:",
        party_options,
        index=party_options.index(default_party))

    default_message = f"Showing KWIC examples for default party: {default_party}"

    kwic_output = generate_kwic(df, query_lemma=lemma, selected_party=clicked_party)
    
    if len(kwic_output) > 0:
        for example in kwic_output:
            st.write(example)
    else:
        st.write(f'Im Wahlprogramm {flection[clicked_party]} kommt das Wort "{lemma}" nicht vor.')

    collo = get_collocations(df, query_lemma=lemma, selected_party=clicked_party)
    collo_filtered = collo[(collo["LogRatio"] > 0) & (collo["freq"] > 2)]
    collo_filtered.rename(columns={"lemma":"Lemma","freq":"Collocate Frequency"}, inplace=True)
    collo_filtered = collo_filtered[["Lemma","Collocate Frequency","LogRatio"]].sort_values(by="LogRatio", ascending=False)
    
    if len(collo_filtered) > 0:
        with st.expander(f"Kollokationen von '{lemma}' im Programm {flection[clicked_party]} anzeigen"):
            st.dataframe(collo_filtered)

    st.divider()

    # Print link to original text
    st.write(f"Das ganze Wahlprogramm {flection[clicked_party]} kann [hier]({programs[clicked_party]}) eingesehen werden.")

    st.divider()

with st.expander("Für Informationen zu diesem Tool hier klicken!"):
    st.write("""
    ### Daten und Methode

    Dieses interaktive Tool erlaubt die Abfrage von Worthäufigkeiten in den Wahlprogrammen zur Bundestagswahl 2025. Datengrundlage sind die Wahlprogramme im PDF-Format, die in ein txt-Format überführt und manuell bereinigt wurden. Für die Korrektheit dieser Aufbereitung wird keine Garantie übernommen. Für die linguistische Vorverarbeitung (Tokenisierung und Lemmatisierung) wurde der TreeTagger genutzt.

    **Was zeigen die Balkendiagramme und wie sind sie zu lesen?**
    
    Die Balkendiagramme zeigen relative Häufigkeiten (Treffer pro Millionen Wörter), d.h. die absoluten Häufigkeiten auf die auf die jeweils unterschiedlichen Umfänge der Wahlprogramme skaliert, damit sie untereinander vergleichbar werden. Bei der mittelwertzentrierten Darstellung wird als Nullpunkt der Mittelwert angezeigt. Zeigt ein Balken nach oben, verwendet die Partei das Wort häufiger als der parteiübergreifende Durchschnitt, zeigt er nach unten, verwendet sie es seltener.

    Durch Anklicken der Balken können die absoluten Häufigkeiten angezeigt werden, außerdem können die zugrundeliegenden Daten in Tabellenform ausgegeben werden.

    **Wichtig**: Bei der Interpretation muss man beachten, dass die An- und Abwesenheit von *Wörtern* nur zum Teil etwas über die Relevanz der mit diesen Wörtern bezeichneten *Themen* im jeweiligen Parteiprogramm aussagen kann. Einen ersten Eindruck über die parteispezifische Nutzung und Bedeutung der Wörter vermitteln die Beispielbelege. Für ein abschließendes Urteil ist zudem ein Blick in die (jeweils unten verlinkten) Originaltexte unumgänglich.

    **Was sind Kollokationen?**

    Bei hinreichend frequenten Wörtern werden unter den Beispielbelegen auch Kollokationen angezeigt. Das sind Wörter, die im unmittelbaren Kontext des Suchwortes relativ häufiger vorkommen als im restlichen Text. Kollokationen zeigen also häufige Wortkombinationen an (etwa 'soziale Gerechtigkeit') und können im Verbund einen Eindruck von parteispezifischen Wortgebräuchen vermitteln. Das genutzte Assoziationsmaß ist LogRatio (die logarithmierte Ratio der relativen Häufigkeiten) bei einer Kontextgröße von 5 Wörtern links und rechts und eine Mindestfrequenz von 3.

    Feedback gerne an [simon.meier-vieracker@tu-dresden.de](mailto:simon.meier-vieracker@tu-dresden.de). Das Analyseskript kann auf GitHub eingesehen werden, Anpassungs- und Erweiterungsvorschläge sind sehr willkommen.
    """)
