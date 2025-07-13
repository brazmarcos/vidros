import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State, ALL
import dash_bootstrap_components as dbc
import os

# Caminho relativo (assumindo que o CSV está na mesma pasta do script)
caminho_arquivo = os.path.join(os.path.dirname(__file__), "vid_input.csv")
dados = pd.read_csv(caminho_arquivo)


# Garantir que os códigos HEX são válidos
dados['HEX'] = dados['HEX'].apply(lambda x: f'#{x}' if not str(x).startswith('#') else str(x))

# Função para formatar custo
def formatar_custo(valor):
    try:
        if pd.isna(valor) or float(valor) == 0:
            return "Custo não informado"
        return f"R$ {float(valor):,.2f}"
    except:
        return "Custo não informado"

# Criar app Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Dashboard de Vidros"

# Layout
app.layout = dbc.Container([
    dcc.Store(id='store-selected-data', data=[]),
    
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Vidros - Análise de Desempenho"), 
               width=12, className="text-center my-4")
    ]),
    
    dbc.Row([
        # Coluna de filtros
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Filtros", className="card-title"),
                    
                    html.Label("Tipo de Vidro:", className="fw-bold mt-2"),
                    dcc.Checklist(
                        id='tipo-vidro',
                        options=[
                            {'label': ' Laminado', 'value': 'Laminado'},
                            {'label': ' Insulado', 'value': 'Insulado'}
                        ],
                        value=['Laminado', 'Insulado'],
                        labelStyle={'display': 'block', 'margin': '5px'}
                    ),
                    
                    html.Label("Faixa de Fator Solar (0-100):", className="fw-bold mt-3"),
                    dcc.RangeSlider(
                        id='fator-solar-range',
                        min=0,
                        max=100,
                        step=1,
                        value=[0, 100],
                        marks={i: str(i) for i in range(0, 101, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    
                    html.Label("Faixa de Transmitância (0-100):", className="fw-bold mt-3"),
                    dcc.RangeSlider(
                        id='transmitancia-range',
                        min=0,
                        max=100,
                        step=1,
                        value=[0, 100],
                        marks={i: str(i) for i in range(0, 101, 10)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    
                    html.Div(id='info-box', className="mt-4 p-3 bg-light rounded")
                ])
            ], className="mb-4")
        ], md=3),
        
        # Coluna do gráfico e tabela
        dbc.Col([
            dbc.Row([
                dbc.Col(
                    dcc.Graph(
                        id='scatter-plot',
                        figure=px.scatter().update_layout(
                            xaxis={'visible': False},
                            yaxis={'visible': False},
                            plot_bgcolor='rgba(240,240,240,0.8)'
                        ),
                        style={'height': '60vh'},
                        config={'displayModeBar': False}
                    ),
                    width=8
                ),
                
                dbc.Col([
                    html.Div([
                        html.H5("Vidros Selecionados", className="d-inline"),
                        dbc.Button("Limpar Todos", 
                                 id="limpar-todos", 
                                 color="danger", 
                                 size="sm", 
                                 className="ms-2 mb-2")
                    ], className="mb-3 text-center"),
                    
                    dash_table.DataTable(
                        id='tabela-selecionados',
                        columns=[
                            {'name': 'Fabricante', 'id': 'Fabricante'},
                            {'name': 'Modelo', 'id': 'Modelo'},
                            {'name': 'Tipo', 'id': 'Tipo de vidro'},
                            {'name': 'Fator Solar', 'id': 'Fator Solar'},
                            {'name': 'Transmitância', 'id': 'Transmitancia Luminosa'},
                            {'name': 'Fator U', 'id': 'Fator U'},
                            {'name': 'Custo', 'id': 'Custo'},
                            {'name': '', 'id': 'remover', 'presentation': 'markdown'}
                        ],
                        data=[],
                        style_table={'overflowX': 'auto', 'height': '400px', 'overflowY': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '8px',
                            'fontSize': '12px',
                            'whiteSpace': 'normal'
                        },
                        style_header={
                            'backgroundColor': 'lightgrey',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        markdown_options={'html': True}
                    )
                ], width=4)
            ]),
            
            dbc.Row([
                dbc.Col(
                    html.Div(id='total-registros', className="text-center fw-bold mt-3 p-2 bg-light rounded"),
                    width=12
                )
            ])
        ], md=9)
    ])
], fluid=True)

# Callback para atualizar o gráfico
@app.callback(
    [Output('scatter-plot', 'figure'),
     Output('total-registros', 'children'),
     Output('info-box', 'children'),
     Output('store-selected-data', 'data')],
    [Input('tipo-vidro', 'value'),
     Input('fator-solar-range', 'value'),
     Input('transmitancia-range', 'value'),
     Input('limpar-todos', 'n_clicks')],
    [State('store-selected-data', 'data')]
)
def update_graph(tipos_selecionados, fator_solar_range, transmitancia_range, limpar_clicks, stored_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger_id = None
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Limpar seleção se o botão foi clicado
    if trigger_id == 'limpar-todos':
        stored_data = []
    
    fs_min, fs_max = fator_solar_range
    tl_min, tl_max = transmitancia_range
    
    # Aplicar filtros
    if not tipos_selecionados:
        dados_filtrados = dados.copy()
        tipo_info = "Mostrando todos os tipos de vidro"
    else:
        dados_filtrados = dados[dados['Tipo de vidro'].isin(tipos_selecionados)]
        tipo_info = f"Tipos selecionados: {', '.join(tipos_selecionados)}"
    
    dados_filtrados = dados_filtrados[
        (dados_filtrados['Fator Solar'] >= fs_min) & 
        (dados_filtrados['Fator Solar'] <= fs_max) &
        (dados_filtrados['Transmitancia Luminosa'] >= tl_min) & 
        (dados_filtrados['Transmitancia Luminosa'] <= tl_max)
    ].copy()
    
    # Informações de filtro
    filtro_info = [
        html.P(tipo_info),
        html.P(f"Fator Solar: {fs_min} a {fs_max}"),
        html.P(f"Transmitância: {tl_min} a {tl_max}")
    ]
    
    # Calcular tamanhos dos marcadores
    tamanho_min = 10
    tamanho_max = 40
    
    if not dados_filtrados.empty:
        # Normalizar custo para tamanho dos marcadores
        custo_min = dados_filtrados['Custo'].min()
        custo_max = dados_filtrados['Custo'].max()
        
        if custo_max > custo_min:  # Evitar divisão por zero
            dados_filtrados['Tamanho'] = tamanho_min + (tamanho_max - tamanho_min) * (
                (dados_filtrados['Custo'] - custo_min) / (custo_max - custo_min))
        else:
            dados_filtrados['Tamanho'] = tamanho_min
            
        # Preencher NA com valor intermediário
        dados_filtrados['Tamanho'] = dados_filtrados['Tamanho'].fillna((tamanho_min + tamanho_max)/2)
    else:
        # Se não houver dados, criar coluna vazia
        dados_filtrados['Tamanho'] = tamanho_min
    
    # Criar gráfico de dispersão
    if not dados_filtrados.empty:
        fig = px.scatter(
            dados_filtrados,
            x='Fator Solar',
            y='Transmitancia Luminosa',
            color='HEX',
            color_discrete_map={hex_val: hex_val for hex_val in dados_filtrados['HEX'].unique()},
            size='Tamanho',
            custom_data=['Fabricante', 'Modelo', 'Tipo de vidro', 'Fator Solar', 
                        'Transmitancia Luminosa', 'Fator U', 'Reflexao externa', 
                        'Reflexao interna', 'Custo', 'Aspecto', 'HEX'],
            title=None
        )
        
        # Destacar pontos selecionados
        if stored_data:
            fig.update_traces(
                selectedpoints=[i['pointIndex'] for i in stored_data],
                selected={'marker': {'size': 15, 'opacity': 1}}
            )
        
        fig.update_layout(
            xaxis_title='Fator Solar (0-100)',
            yaxis_title='Transmitância Luminosa (0-100)',
            plot_bgcolor='rgba(240,240,240,0.8)',
            hovermode='closest',
            showlegend=False,
            clickmode='event+select'
        )
        
        # Tooltip
        fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]} - %{customdata[1]}</b><br>"
                "<b>Tipo:</b> %{customdata[2]}<br>"
                "<b>Fator Solar:</b> %{customdata[3]:.1f}<br>"
                "<b>Transmitância:</b> %{customdata[4]:.1f}<br>"
                "<b>Fator U:</b> %{customdata[5]}<br>"
                "<b>Reflexão Externa:</b> %{customdata[6]}<br>"
                "<b>Reflexão Interna:</b> %{customdata[7]}<br>"
                "<b>Custo:</b> %{customdata[8]}<br>"
                "<b>Aspecto:</b> %{customdata[9]}<br>"
                "<b>Cor:</b> %{customdata[10]}"
            ),
            marker=dict(
                line=dict(width=0.5, color='DarkSlateGrey'),
                opacity=0.8
            )
        )
    else:
        # Gráfico vazio se não houver dados
        fig = px.scatter().update_layout(
            xaxis={'visible': False},
            yaxis={'visible': False},
            plot_bgcolor='rgba(240,240,240,0.8)',
            annotations=[{
                'text': 'Nenhum dado encontrado com os filtros atuais',
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
    
    total = len(dados_filtrados)
    mensagem = f"Total de vidros encontrados: {total}"
    
    return fig, mensagem, filtro_info, stored_data

# Callback para lidar com seleção de pontos
@app.callback(
    Output('store-selected-data', 'data', allow_duplicate=True),
    Input('scatter-plot', 'selectedData'),
    State('store-selected-data', 'data'),
    prevent_initial_call=True
)
def update_selected_data(selected_data, stored_data):
    if not selected_data or 'points' not in selected_data:
        return dash.no_update
    
    new_points = selected_data['points']
    current_points = stored_data.copy()
    
    # Adicionar novos pontos (sem limite)
    for point in new_points:
        if not any(p['pointIndex'] == point['pointIndex'] for p in current_points):
            current_points.append({
                'pointIndex': point['pointIndex'],
                'customdata': point['customdata'],
                'id': len(current_points)  # ID único para cada seleção
            })
    
    return current_points

# Callback para atualizar a tabela de selecionados
@app.callback(
    [Output('tabela-selecionados', 'data'),
     Output('tabela-selecionados', 'columns')],
    [Input('store-selected-data', 'data'),
     Input({'type': 'remover-vidro', 'index': ALL}, 'n_clicks')],
    [State('store-selected-data', 'data')]
)
def update_table(selected_data, remove_clicks, current_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger_id = None
    else:
        trigger_id = ctx.triggered[0]['prop_id']
    
    # Verificar se foi um clique em um botão de remoção
    if trigger_id and 'remover-vidro' in trigger_id:
        trigger_index = eval(ctx.triggered[0]['prop_id'].split('.')[0])['index']
        # Remover o item correspondente
        selected_data = [item for item in current_data if item['id'] != trigger_index]
    
    if not selected_data:
        return [], [
            {'name': 'Fabricante', 'id': 'Fabricante'},
            {'name': 'Modelo', 'id': 'Modelo'},
            {'name': 'Tipo', 'id': 'Tipo de vidro'},
            {'name': 'Fator Solar', 'id': 'Fator Solar'},
            {'name': 'Transmitância', 'id': 'Transmitancia Luminosa'},
            {'name': 'Fator U', 'id': 'Fator U'},
            {'name': 'Custo', 'id': 'Custo'},
            {'name': '', 'id': 'remover', 'presentation': 'markdown'}
        ]
    
    # Preparar dados para a tabela
    table_data = []
    for item in selected_data:
        data = item['customdata']
        table_data.append({
            'Fabricante': data[0],
            'Modelo': data[1],
            'Tipo de vidro': data[2],
            'Fator Solar': f"{float(data[3]):.1f}",
            'Transmitancia Luminosa': f"{float(data[4]):.1f}",
            'Fator U': data[5],
            'Custo': formatar_custo(data[8]),
            'remover': f"<button class='btn btn-sm btn-outline-danger' id='{ {'type': 'remover-vidro', 'index': item['id']} }'>×</button>"
        })
    
    columns=[
        {'name': 'Fabricante', 'id': 'Fabricante'},
        {'name': 'Modelo', 'id': 'Modelo'},
        {'name': 'Tipo', 'id': 'Tipo de vidro'},
        {'name': 'Fator Solar', 'id': 'Fator Solar'},
        {'name': 'Transmitância', 'id': 'Transmitancia Luminosa'},
        {'name': 'Fator U', 'id': 'Fator U'},
        {'name': 'Custo', 'id': 'Custo'},
        {'name': '', 'id': 'remover', 'presentation': 'markdown'}
    ]
    
    return table_data, columns

if __name__ == '__main__':
    app.run(debug=True)

server = app.server  # Permite que o Render reconheça como aplicação web
