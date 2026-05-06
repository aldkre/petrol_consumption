import plotly.express as px

def plot_metric(df, group_col, value_col, agg, sort_asc, n, color):
    df_plot = (
        df.groupby(group_col)[value_col]
        .agg(agg)
        .sort_values(ascending=sort_asc)
        .head(n)
        .reset_index()
    )

    fig = px.bar(
        df_plot,
        x=value_col,
        y=group_col,
        orientation="h",
        color_discrete_sequence=[color],
    )

    fig.update_traces(hovertemplate="Pojazd = %{y}<extra></extra>")
    return fig
