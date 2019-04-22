





cmd = "bzip2 -d " + file_name
url = "http://data.caida.org/datasets/as-relationships/serial-2/20190401.as-rel2.txt.bz2"
df = pd.read_csv(url,
                 compression='bz2',
                 sep='|',
                 low_memory=False,
                 header=None)
df.loc[df[3] == 'bgp']
df = df[[0,1,2]]
df[2] = df[2].astype(int)
df[2].rename(columns={0:'as1',
                      1:'as2',
                      2:'relation'},
             inplace=True)
