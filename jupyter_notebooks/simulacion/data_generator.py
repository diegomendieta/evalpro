import pandas as pd


def create_filtered_dataframe(file, HUB, n_skus):
    datos_limpios = pd.read_csv(file)
    datos_limpios = datos_limpios.drop(columns='Unnamed: 0')
    datos_limpios_HUB = datos_limpios[datos_limpios['HUB'] == HUB]

    top_skus = datos_limpios_HUB.groupby(
        by=['ID_SKU_VENTA']).sum().reset_index()
    top_n_skus = top_skus.sort_values(by='Venta en pallets',
                                      ascending=False).head(n_skus)
    top_n_skus_list = list(top_n_skus['ID_SKU_VENTA'])

    datos_limpios_HUB_SKUS = datos_limpios_HUB[
        datos_limpios_HUB['ID_SKU_VENTA'].isin(top_n_skus_list)]

    return datos_limpios_HUB_SKUS


def simulation_generator(dataframe, sS_dict, sku, cd):
    sS_info = sS_dict[(sku, cd)]

    dataframe = dataframe[
        (dataframe['ID_SKU_VENTA'] == sku) & (dataframe['DESCR_CENDIST'] == cd)]

    for index, row in dataframe.iterrows():
        yield row['Venta en pallets'], sS_info[0], sS_info[1]


def stats(dataframe, confianza, lead_times_dict, S_factor_dict):
    mean_no_group = dataframe.groupby(
        by=['ID_SKU_VENTA', 'DESCR_CENDIST']).mean().reset_index().rename(
        columns={'Venta en pallets': 'MEDIA'})
    stdev_no_group = dataframe.groupby(
        by=['ID_SKU_VENTA', 'DESCR_CENDIST']).std().reset_index().rename(
        columns={'Venta en pallets': 'STD'})

    mean_no_group['MEDIA'] = mean_no_group.apply(
        lambda x: x.MEDIA * lead_times_dict[x['DESCR_CENDIST']], axis=1)
    stdev_no_group['STD'] = stdev_no_group.apply(
        lambda x: x.STD * lead_times_dict[x['DESCR_CENDIST']], axis=1)

    data_completa = mean_no_group.merge(stdev_no_group,
                                        on=['ID_SKU_VENTA', 'DESCR_CENDIST'])

    data_completa['s'] = data_completa.apply(lambda x: x['MEDIA'] +
                                                       confianza * x['STD'],
                                             axis=1)

    data_completa['S'] = data_completa.apply(
        lambda x: x['s'] * int(S_factor_dict[str(x['ID_SKU_VENTA'])]), axis=1)

    return data_completa.drop(columns=['MEDIA', 'STD'])


def create_sS_dict(dataframe):
    sS_dict = {}

    for index, row in dataframe.iterrows():
        sS_dict[(row['ID_SKU_VENTA'], row['DESCR_CENDIST'])] = (
        row['s'], row['S'])

    return sS_dict


