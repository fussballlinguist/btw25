import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

st.markdown("""
    <style>
        svg text {
            text-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

today_date = datetime.today().strftime("%d.%m.%Y")

st.write("### Nominalkomposita in Bundestagswahlprogrammen")
st.write(f"Ein Tool von [Simon Meier-Vieracker](https://tu-dresden.de/gsw/slk/germanistik/al/die-professur/inhaber), Stand {today_date}")

def sankey(source_indices, target_indices, components, component):

	custom_data = []
	link_values = []

	df_composites = pd.DataFrame(columns=["Lemma", "Frequenz"])

	for src, tgt in zip(source_indices, target_indices):
		first = components[src]
		second = components[tgt]

		match = df[(df["firsts"] == first) & (df["seconds"] == second)]

		if not match.empty:
			lemma = match["lemma"].iloc[0]
			freq = match["freq"].iloc[0]
		else:
			lemma = "N/A"
			freq = 0

		custom_data.append(f"{lemma}; Frequenz: {freq}")

		df_composites.loc[len(df_composites)] = [lemma, freq]
		
	fig = go.Figure(data=[go.Sankey(
	  node = dict(
		pad = 10,
		thickness = 10,
		line = dict(color = "black", width = 1),
		label = components,
		color = "orchid"
		#sort="none"
	  ),
	  link = dict(
		source=source_indices,
		target=target_indices,
		value = [1] * (len(components) - 1),
		customdata=custom_data,  # Pass extracted lemma and freq data
		hovertemplate="Lemma: %{customdata}<extra></extra>",
		color="lavenderblush"
	))])

	fig.update_layout(
	  title_text=f"Nominalkomposita mit <i>{component}</i>",
	  font_size=14,
	  width=500,  # Increase width
	  height=len(components) * 21
	  #font_color="blue",
	)
	st.plotly_chart(fig, use_container_width=True, theme=None)
	st.dataframe(df_composites, use_container_width=False)

corpus = pd.read_csv("btw25_corrected.tsv", sep="\t", quoting=3)
df_lemma = corpus.groupby("lemma").size().reset_index(name="freq")

df = pd.read_csv("nn_splits.tsv", sep="\t", header=None)
df.columns = ["hierarchy","bool","nan","hierarchy_int","lemma","lemma_split","components","component_brackets"]
df = df[df["hierarchy_int"] == 2]
df = df.merge(df_lemma, on="lemma")

df["firsts"] = df["components"].str.split().str[0]
df["seconds"] = df["components"].str.split().str[1]
df = df[df['firsts'].str.match(r'^[A-Z]')]
df = df[df['seconds'].str.match(r'^[A-Z]')]

top_firsts = list(df['firsts'].value_counts().nlargest(30).index)
remove = ["Ann","Eu","Ei","Vers","De"]
top_firsts = [x for x in top_firsts if x not in remove]
top_seconds = list(df['seconds'].value_counts().nlargest(30).index)

tab1, tab2 = st.tabs(["Nach Erstgliedern", "Nach Zweitgliedern"])

with tab1:
	top_firsts.insert(0, "Bitte Erstglied auswählen")

	component = st.selectbox(
			"",
			#label_visibility = 'hidden',
			top_firsts
			)

	if component != "Bitte Erstglied auswählen":
		firsts = [component]
		df_filtered = df[df["firsts"].isin(firsts)]
		seconds = sorted(list(set(df_filtered.seconds)))
		components = firsts + seconds
		component = component + "-"

		source_indices = [0] * (len(components) - 1)
		target_indices = list(range(1, len(components)))

		sankey(source_indices=source_indices, target_indices=target_indices, components=components, component=component)

with tab2:
	top_seconds.insert(0, "Bitte Zweitglied auswählen")

	component = st.selectbox(
			"",
			top_seconds
			)

	if component != "Bitte Zweitglied auswählen":
		seconds = [component]
		df_filtered = df[df["seconds"].isin(seconds)]
		firsts = sorted(list(set(df_filtered.firsts)))
		components = firsts + seconds
		component = "-" + component.lower()

		source_indices = list(range(0, len(components) - 1))
		target_indices = [len(components) - 1] * (len(components) - 1)

		sankey(source_indices=source_indices, target_indices=target_indices, components=components, component=component)

with st.expander("Für Informationen zu diesem Tool hier klicken!"):
    st.write("""
    ### Worum geht es hier?

    Dieses interaktive Tool erlaubt die Abfrage von Nominalkomposita in den Wahlprogrammen zur Bundestagswahl 2025. Möglich ist die Suche nach Komposita mit den jeweils 30 produktivsten Erst- und Zweitgliedern. Beim Berühren der Diagrammlinien können die Häufigkeiten der Nominalkomposita angezeigt werden, unter dem Diagramm werden die Daten zudem in Tabellenform ausgegeben. 

    **Daten und Methode**
    
    Datengrundlage sind die (im Falle der AfD und der Linken vorläufigen) Wahlprogramme im PDF-Format, die in ein txt-Format überführt und manuell bereinigt wurden. Für die Korrektheit dieser Aufbereitung wird keine Garantie übernommen. Für die linguistische Vorverarbeitung (Tokenisierung und Lemmatisierung) wurde der TreeTagger genutzt.

    Für die morphologische Analyse wurden alle Substantive extrahiert und wo möglich mit dem [MOP Compound Splitter](https://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/mcs/) in die Bestandteile zerlegt. In die weitere Auswertung wurden nur reine Nominalkomposita übernommen, die also aus zwei Substantiven zusammengesetzt sind.

    **Es handelt sich um eine Testversion!** Feedback gerne an [simon.meier-vieracker@tu-dresden.de](mailto:simon.meier-vieracker@tu-dresden.de). Das Analyseskript kann auf GitHub eingesehen werden, Anpassungs- und Erweiterungsvorschläge sind sehr willkommen.
    """)
