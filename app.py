###############Impoting libraries###########
from turtle import color, width
import streamlit as st 
import pandas as pd 
import openpyxl 
from streamlit_option_menu import option_menu
import requests
from streamlit_lottie import st_lottie
import time
from deep_translator import GoogleTranslator 
import pyecharts 
from pyecharts.charts import Map,Geo
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from pyecharts.charts import Bar,Tab
from pyecharts.charts import Pie
from pyecharts.charts import Line
from pyecharts.charts import ThemeRiver
from pyecharts.charts import HeatMap
from datetime import datetime
import streamlit_echarts
from streamlit_echarts import st_pyecharts
import streamlit.components.v1 as components
import base64
from io import StringIO, BytesIO  # Standard Python Module
import json
from PIL import Image



################## Function for Dowloading data in excel file###################
def generate_excel_download_link(df):
    # Credit Excel: https://discuss.streamlit.io/t/how-to-add-a-download-excel-csv-function-to-a-button/4474/5
    towrite = BytesIO()
    df.to_excel(towrite, encoding="utf-8", index=False, header=True)  # write to BytesIO buffer
    towrite.seek(0)  # reset pointer
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="data_download.xlsx">Download Excel File</a>'
    return st.markdown(href, unsafe_allow_html=True)


################## Navbar Options ################
with st.sidebar:
  selected = option_menu(
    menu_title= "Main menu",
    menu_icon= "cast",
    options=["Home","Analyze your Data","About","Contact"],
    icons=["house","bar-chart-line-fill","book","envelope"],
    default_index=0,
    orientation="vertical",
    styles={
          "container": {"padding": "0!important", "background-color": "Bisque", "font-family": "Permanent Marker"},
          "icon": {"color": "Brown", "font-size": "25px"}, 
          "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "Brown"},
          "nav-link-selected": {"background-color": "Maroon"},
          
    }
  )

#for animation
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()
lottie_draganddrop = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_2f6i2vl9.json")
lottie_analyse=load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_tljjahng.json")

########### Navbar selections #################
if selected =="Analyze your Data":
  with st.container():
    st.markdown("<h4 style='text-align: center; color: Brown;'>Upload your Excel file here</h4>", unsafe_allow_html=True)
    st_lottie(lottie_draganddrop,height=100)
    uploaded_file = st.file_uploader('', type='xlsx',key='file_uploader')
    if uploaded_file:
        st.markdown('---')
        all_data = pd.read_excel(uploaded_file, engine='openpyxl')
        st.dataframe(all_data) #priting data frame
        all_data.drop('Status',axis=1,inplace=True)
        dcf=all_data.copy()
        dcf = dcf.loc[dcf['client final'].notnull()]
        dcf["Pays"].fillna('AUTRES',inplace=True) #pour atteindre le nombre de commande
        dcf=dcf[dcf['Pays']!='AUTRES']
        option=st.selectbox(
          "What do you like to analyse?",
          ("Orders/Country","Orders/Train","Percentage of merchantable qualities","Merchantable quality/client","Source quality/entity")
        )
        if option =="Orders/Country":
          info_c_p= dcf[dcf['Pays'].notnull()]
          info_c_p=info_c_p.groupby(["Date de réception d'échantillon","Pays"])["Train"].nunique()
          info_c_p=info_c_p.groupby("Pays").sum().to_frame()
          info_c_p.rename(index={"USA":"UNITED STATES","PEROU":"PERU","COREEDUSUD":"KOREA","PAYSBAS":"PAYS-BAS",
                                "SLOVENIE":"SLOVÉNIE","THAIWAN":"THAÏWAN"},inplace=True)
          info_c_p.rename(columns={'Train':'T_Commande'},inplace=True)
          info_c_p.reset_index(inplace=True)
          #translating countries
          gt = GoogleTranslator(source='auto', target='en')
          info_c_p['Pays'] = info_c_p['Pays'].apply(gt.translate)
          #Get the coutries's names normalized
          info_c_p["Pays"]=info_c_p["Pays"].str.lower().str.capitalize().str.title()
          ##################visualization ####################
          country=list(info_c_p['Pays'])
          total_commandes=list(info_c_p['T_Commande'])
          list1 = [[country[i],total_commandes[i]] for i in range(len(country))]
          map_1 =( Map(init_opts=opts.InitOpts(width="1000px", height="460px")) 
            .add("Total Orders", list1, maptype='world') 
            .set_series_opts(label_opts=opts.LabelOpts(is_show=False)) #remove country names
            .set_global_opts(visualmap_opts=opts.VisualMapOpts(max_=600,is_piecewise=True),legend_opts=opts.LegendOpts(is_show=True))
            .render_embed()
          )
          components.html(map_1, width=700, height=700)
          ######### download section #########
          #st.subheader('Download Data')#try text
          st.markdown("<h5 style='text-align: left; color: Brown;'>Download Data</h5>", unsafe_allow_html=True)
          generate_excel_download_link(info_c_p)
        if option =="Orders/Train":
          info_train=dcf[dcf['Train']!=0]
          info_train=info_train.groupby(["Date de réception d'échantillon","Train"])["Train"].nunique()
          info_train=info_train.groupby("Train").sum().to_frame()
          info_train.rename(columns={"Train":"Nombre de commandes"},inplace=True)
          info_train.reset_index(inplace=True)
          # plotting infos about "Trains"
          freq_train=(
              Bar()
              .add_xaxis(info_train["Train"].tolist())
              .add_yaxis('Nombre de trains',info_train["Nombre de commandes"].round(0).tolist())
              .set_global_opts(title_opts=opts.TitleOpts(title="Commandes/Train"))
              #.render_embed()
          )
          #components.html(freq_train, width=700, height=700,scrolling=True)#600 is a test
          st_pyecharts(freq_train, theme=ThemeType.LIGHT)
          generate_excel_download_link(info_train)
        if option =="Percentage of merchantable qualities":
          info_q=dcf[dcf["Qualité"].notnull()]
          info_q=info_q.loc[info_q["Qualité"].str.contains('K')]
          info_q=info_q.groupby(["Date de réception d'échantillon","Qualité"])["Train"].nunique()
          info_q=info_q.groupby("Qualité").sum()
          info_q=info_q.to_frame().rename(columns={"Qualité":"qualité"}).reset_index()
          info_q.rename(columns={"Train":"nbr de commandes"},inplace=True)
          ###################plot###################
          qual=list(info_q["Qualité"])
          val=list(info_q["nbr de commandes"])
          pie = (Pie()
                .add('', [list(z) for z in zip(qual,val)],
                      radius=["30%", "75%"],
                      rosetype="radius")
                .set_global_opts(title_opts=opts.TitleOpts(title="Les qualités marchandes", subtitle="Fréquences de commandes par qualités"),
                                legend_opts=opts.LegendOpts( #rendre la legende verticale
                                                            orient="vertical",
                                                            pos_left="90%",
                                                            type_="scroll"        
                                                            ))
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {d}%"))
                .render_embed()
                )
          components.html(pie, width=700, height=600,scrolling=True) #600 is a test
          #st_pyecharts(pie, theme=ThemeType.LIGHT)
          generate_excel_download_link(info_q)
        if option =="Merchantable quality/client":
          client=st.text_input("veiller entrer le nom du client")
          if client:
            info_varq=dcf[dcf["Qualité"].notnull()]
            info_varq=info_varq.loc[info_varq["Qualité"].str.contains("K")]
            info_varq=info_varq.loc[info_varq["client final"]==client]
            info_varq["Date de réception d'échantillon"]=pd.to_datetime(info_varq["Date de réception d'échantillon"]).dt.date
            #info_varq["Date d'autorisation"]=pd.DatetimeIndex(info_varq["Date d'autorisation"]).date
            info_varq=info_varq.groupby(["Date de réception d'échantillon","Qualité"])["Numero d'echantillon"].nunique()
            info_varq=info_varq.to_frame()
            info_varq.rename(columns={"Numero d'echantillon":"Total des commandes"},inplace=True)
            info_varq.reset_index(inplace=True)
            ############### Visuel #######################
            bar =( Bar()
                  .add_xaxis(list(info_varq["Date de réception d'échantillon"]))
                  .add_yaxis('K02',list(info_varq["Total des commandes"].where(info_varq["Qualité"]=="K02").fillna(0)),stack='stack1')
                  .add_yaxis('K09',list(info_varq["Total des commandes"].where(info_varq["Qualité"]=="K09").fillna(0)),stack='stack1')
                  .add_yaxis('K09 SS',list(info_varq["Total des commandes"].where(info_varq["Qualité"]=="K09 SS").fillna(0)),stack='stack1')
                  .add_yaxis('K09 Local',list(info_varq["Total des commandes"].where(info_varq["Qualité"]=="K09 Local").fillna(0)),stack='stack1')
                  .add_yaxis('K10',list(info_varq["Total des commandes"].where(info_varq["Qualité"]=="K10").fillna(0)),stack='stack1')
                  .add_yaxis('K12',list(info_varq["Total des commandes"].where(info_varq["Qualité"]=="K12").fillna(0)),stack='stack1')
                  .add_yaxis('K20',list(info_varq["Total des commandes"].where(info_varq["Qualité"]=="K20").fillna(0)),stack='stack1')
                  .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
                  .set_global_opts(
                        title_opts = opts.TitleOpts(title='Qualités commandées par '+client),
                        datazoom_opts= opts.DataZoomOpts(
                            is_show=True,#display
                            is_realtime=True,
                            range_end= 60, 
                        ),
                      legend_opts=opts.LegendOpts( #rendre la legende verticale
                                    orient="vertical",
                                    pos_left="90%",
                                    type_="scroll"        
                                ),
                      tooltip_opts=opts.TooltipOpts(
                                            is_show=True,
                                            trigger='axis',  # Axis triggering, mainly for column and line charts
                                            trigger_on='mousemove|click',  # Triggered when the mouse moves and clicks simultaneously.
                                        )
                  )
            )
            st_pyecharts(bar, theme=ThemeType.LIGHT, height="500px",width="100%")
        if option =="Source quality/entity":
          zone=st.text_input("veiller entrer le nom de la zone")
          if zone:
            var_elm=all_data.copy()
            var_elm=var_elm.loc[var_elm["Client"]==zone]
            var_elm["Date de réception d'échantillon"]=var_elm["Date de réception d'échantillon"].apply(lambda x : datetime.strptime(x, '%d/%m/%Y %H:%M:%S').date())#pour prendre seulement j/m/a
            var_elm=var_elm.groupby(["Date de réception d'échantillon","Nom"])["Résultat"].mean()
            var_elm=var_elm.to_frame().reset_index()
            var_elm["Date de réception d'échantillon"]=var_elm["Date de réception d'échantillon"].apply(lambda x: x.strftime('%Y/%m/%d'))
            var_elm=var_elm.reindex(columns=["Date de réception d'échantillon","Résultat","Nom"])
            ################### Plot ##########################
            d=var_elm.values.tolist()
            river = (
                ThemeRiver()
                .add(
                    series_name=["BPL","Cd_NE","Cd","CO2","SiO2 T","H2O","MgO","SiO2 R","Al2O3","Fe2O3"],
                    data=d,
                    singleaxis_opts=opts.SingleAxisOpts(type_="time")
                )
                .set_global_opts(
                        title_opts = opts.TitleOpts(title='La variation des élement de la zone : '+zone),
                        datazoom_opts= opts.DataZoomOpts(
                            is_show=True,#display
                            is_realtime=True,
                            range_end= 60, 
                        ),
                      legend_opts=opts.LegendOpts( #rendre la legende verticale
                                    orient="vertical",
                                    pos_left="90%",
                                    type_="scroll"        
                                ),
                    tooltip_opts=opts.TooltipOpts(
                                            is_show=True,
                                            trigger='axis',  # Axis triggering, mainly for column and line charts
                                            trigger_on='mousemove|click' # Triggered when the mouse moves and clicks simultaneously.
                                        )
                )
                #.render_embed()
            )
            #components.html(river, width=700, height=600)
            st_pyecharts(river, theme=ThemeType.LIGHT, height="500px",width="100%")
            generate_excel_download_link(var_elm)

if selected =="Home":
    with st.container():
      left_column,right_column=st.columns(2)
      with left_column:
        st.write("##")
        st.write("##")
        st.write("##")
        st.write("##")
        st.markdown("<h3 style='text-align: center; color: Brown;'>Welcome to your DATA Visualization App</h3>", unsafe_allow_html=True)
      with right_column:
        st_lottie(lottie_analyse, height=300)
    with st.container():
        st.write("---")
        st.markdown("<h4 style='text-align: left; color: Brown;'>USER GUIDE</h4>", unsafe_allow_html=True)
        st.write("##")
        st.write(
            """
            On this Web Application you can :
            - Enter your excel file "LIMS" and visualize your data by clicking on "Analyse your Data" button.
            - Know more about the contest of this project in the "About" section.
            - Click on "Contact" to get in touch with the project manager.
            """
        )

if selected =="About":
    image = Image.open('eensias.png')
    st.image(image, width=600)
    st.write(
            """
            As part of our end-of-year internship at the National Superior School of Computing and
            Analysis of Systems (ENSIAS) I had done my internship in the Chemical manufacturing com-
            pany OCP , world leader in the phosphate sector.
            The OCP Group is committed to improving the operational efficiency of its activities integra-
            ted value chain, in order to maintain its position as a leader in the phosphat market, through
            including the implementation of new technologies, processes and production methods.
            Projects in this direction include the Slurry Pipeline, which was commissioned in 2014 on
            the integrated chain from Khouribga’s mine site to the industrial platform of Jorf Lasfar, desi-
            gnated by the North Axis chain.
            The aim of this project is to process and analyse the data of the source and merchentable
            qualities. It also aims to analyse, design and implement an aid system decision-making, with a
            simple and friendly analysis and reporting tool.

            """
        )

if selected =="Contact":
    st.header(":mailbox: Get In Touch With Me!")
    contact_form = """
    <form action="https://formsubmit.co/CHAIMAA.ELACHCHACHI7@GMAIL.COM" method="POST">
        <input type="hidden" name="_captcha" value="false">
        <input type="text" name="name" placeholder="Your name" required>
        <input type="email" name="email" placeholder="Your email" required>
        <textarea name="message" placeholder="Your message here"></textarea>
        <button type="submit">Send</button>
    </form>
    """

    st.markdown(contact_form, unsafe_allow_html=True)

    # Use Local CSS File
    def local_css(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


    local_css("style.css")
