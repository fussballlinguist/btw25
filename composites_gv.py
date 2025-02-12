import streamlit as st
import graphviz
from datetime import datetime
import pandas as pd

def create_graph(firsts, seconds, component, parties):

    st.write(f"### Nominalkomposita mit _{component}_")
    if len(parties) == 1:
        st.write(f'im Wahlprogramm von: {", ".join(parties)}')    
    else:
        st.write(f'in den Wahlprogrammen von: {", ".join(parties)}')

    # Create Graphviz graph
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR', nodesep='0.001', ranksep='1', splines='polyline', labeljust='r')

    if isinstance(firsts, list):
        dot.node(seconds, shape='plain', align='right')
        for first in firsts:
            dot.node(first, shape='plain', align='left')
            dot.edge(first, seconds, arrowhead="none", color="pink")
    elif isinstance(seconds, list):
        dot.node(firsts, shape='plain', align='left')
        for second in seconds:
            dot.node(second, shape='plain')
            dot.edge(firsts, second, arrowhead="none", color="pink", align='right')

    st.graphviz_chart(dot, use_container_width=False)

today_date = datetime.today().strftime("%d.%m.%Y")

st.write("### Nominalkomposita in Bundestagswahlprogrammen")
st.write(f"Ein Tool von [Simon Meier-Vieracker](https://tu-dresden.de/gsw/slk/germanistik/al/die-professur/inhaber), Stand {today_date}")

corpus = pd.read_csv("btw25_corrected.tsv", sep="\t", quoting=3)
#df_lemma_party = corpus.groupby(["lemma"])["party"].size().reset_index(name="freq")

parties = sorted(corpus["party"].unique())

# Initialize session state if not already set
if "selected_parties" not in st.session_state:
    st.session_state.selected_parties = {party: True for party in parties}

# Function to update selection state
def update_selection():
    st.session_state.selected_parties_list = [
        party for party, selected in st.session_state.selected_parties.items() if selected
    ]

# Create columns for layout
num_cols = 3

with st.expander("Parteien auswählen"):
    cols = st.columns(num_cols)


# Display checkboxes in a grid
    for idx, party in enumerate(parties):
        col = cols[idx % num_cols]  # Cycle through columns
        st.session_state.selected_parties[party] = col.checkbox(
            party, value=st.session_state.selected_parties[party], key=party, on_change=update_selection
        )

# Ensure the selected list updates
update_selection()

df_lemma = corpus.groupby("lemma").size().reset_index(name="freq")
df_lemma_party = corpus.groupby(["lemma","party"]).size().reset_index(name="freq")
df_lemma_party = df_lemma_party[df_lemma_party["party"].isin(st.session_state.selected_parties_list)]
lemmas = df_lemma_party["lemma"].unique()

df = pd.read_csv("nn_splits.tsv", sep="\t", header=None)
df.columns = ["hierarchy","bool","nan","hierarchy_int","lemma","lemma_split","components","component_brackets"]
df = df[df["hierarchy_int"] == 2]
df = df.merge(df_lemma_party, on="lemma")

df["firsts"] = df["components"].str.split().str[0]
df["seconds"] = df["components"].str.split().str[1]
df = df[df['firsts'].str.match(r'^[A-Z]')]
df = df[df['seconds'].str.match(r'^[A-Z]')]

top_firsts = list(df['firsts'].value_counts().nlargest(50).index)
remove = ["Ann","Eu","Ei","Vers","De","Minden","Ente"]
top_firsts = [x for x in top_firsts if x not in remove]
top_seconds = list(df['seconds'].value_counts().nlargest(50).index)

tab1, tab2 = st.tabs(["Nach Erstgliedern", "Nach Zweitgliedern"])

with tab1:
    top_firsts.insert(0, "Bitte Erstglied auswählen")

    component = st.selectbox(
            "",
            top_firsts
            )

    if component != "Bitte Erstglied auswählen":
        firsts = component
        df_filtered = df[(df["firsts"].isin([firsts])) & df["lemma"].isin(lemmas)]
        seconds = sorted(list(set(df_filtered.seconds)))
        component = component + "-"

        create_graph(firsts=firsts, seconds=seconds, component=component, parties=st.session_state.selected_parties_list)

        st.divider()

        df_out = df_filtered[['lemma', 'freq']].reset_index(drop=True)
        df_out_combined = df_out.groupby("lemma", as_index=False)["freq"].sum()
        st.dataframe(df_out_combined)

with tab2:
    top_seconds.insert(0, "Bitte Zweitglied auswählen")

    component = st.selectbox(
            "",
            top_seconds
            )

    if component != "Bitte Zweitglied auswählen":
        seconds = component
        df_filtered = df[df["seconds"].isin([seconds])]
        firsts = sorted(list(set(df_filtered.firsts)))
        component = "-" + component.lower()

        create_graph(firsts=firsts, seconds=seconds, component=component, parties=st.session_state.selected_parties_list)

        st.divider()

        df_out = df_filtered[['lemma', 'freq']].reset_index(drop=True)
        df_out_combined = df_out.groupby("lemma", as_index=False)["freq"].sum()
        st.dataframe(df_out_combined)

with st.expander("Für Informationen zu diesem Tool hier klicken!"):
    st.write("""
    ### Worum geht es hier?

    Dieses interaktive Tool erlaubt die Abfrage von Nominalkomposita in den Wahlprogrammen zur Bundestagswahl 2025. Möglich ist die Suche nach Komposita mit den jeweils 50 produktivsten Erst- und Zweitgliedern, zudem können gezielt die Programme einzelner Parteien ausgewertet werden.  Der Graph listet die Glieder alphabetisch, unter dem Diagramm werden die Frequenzen in Tabellenform ausgegeben. Um bestimmte Ausdrücke im Kontext zu sehen, sei das Tool [btw25frequencies](https://btw25frequencies.streamlit.app/) empfohlen.

    **Daten und Methode**
    
    Datengrundlage sind die (im Falle der AfD und der Linken vorläufigen) Wahlprogramme im PDF-Format, die in ein txt-Format überführt und manuell bereinigt wurden. Für die Korrektheit dieser Aufbereitung wird keine Garantie übernommen. Für die linguistische Vorverarbeitung (Tokenisierung und Lemmatisierung) wurde der TreeTagger genutzt.

    Für die morphologische Analyse wurden alle Substantive extrahiert und wo möglich mit dem [MOP Compound Splitter](https://www.ims.uni-stuttgart.de/forschung/ressourcen/werkzeuge/mcs/) in die Bestandteile zerlegt. Das automatisierte Verfahren ist fehleranfällig, in seltenen Fällen werden einfache Substantive fälschlicherweise zerlegt. In die weitere Auswertung wurden nur reine Nominalkomposita übernommen, die also aus zwei Substantiven zusammengesetzt sind. 

    **Es handelt sich um eine Testversion!** Feedback gerne an [simon.meier-vieracker@tu-dresden.de](mailto:simon.meier-vieracker@tu-dresden.de). Das Analyseskript kann auf GitHub eingesehen werden, Anpassungs- und Erweiterungsvorschläge sind sehr willkommen.
    """)

