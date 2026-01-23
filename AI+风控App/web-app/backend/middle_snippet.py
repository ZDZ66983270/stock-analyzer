
        close_col = "收盘"
        if open_col in df.columns and close_col in df.columns:
            for i in range(1, len(df)):
                try:
                    if float(df.iloc[i][open_col]) == 0:
                        col_idx = df.columns.get_loc(open_col)
                        df.iloc[i, col_idx] = df.iloc[i-1][close_col]
                except Exception:
                    continue
        return df

