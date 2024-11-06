import os
import pandas as pandas


def read_all_csv_files(folder_path):
    all_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            df = pandas.read_csv(file_path)
            all_data.append(df)
            print(f"{filename} : {df.shape[0]}")
    return all_data


if not os.path.exists('res'):
    os.mkdir('res')

# 示例用法
all_dfs = read_all_csv_files('data')
sum_count = [df.shape[0] for df in all_dfs]
print(sum(sum_count))

data = {
    'instruction': [],
    'input': [],
    'output': []
}
for df in all_dfs:
    # 评论ID,父评论ID,用户昵称,用户ID,评论内容,发布时间,点赞数
    for _, row in df.iterrows():
        cid = row['评论ID']
        pcid = row['父评论ID']
        nickname = row['用户昵称']
        userid = row['用户ID']
        content = row['评论内容']
        pubdate = row['发布时间']
        likes = row['点赞数']

        if pandas.isna(content):
            continue

        if pandas.isna(pcid):
            sub = df[df['父评论ID'] == int(cid)]
            if sub.shape[0] <= 0:
                data['instruction'].append(None)
                data['input'].append(None)
                data['output'].append(content)
            else:
                for _, subrow in sub.iterrows():
                    sub_content = subrow['评论内容']
                    if pandas.isna(sub_content):
                        continue

                    data['instruction'].append(content)
                    data['input'].append(None)
                    data['output'].append(sub_content)
        # else:
        # p = df[df['评论ID'] == int(pcid)]
        # p = df.iloc[int(pcid)]
        # p = df.query(f'评论ID = {int(pcid)}')
        # data['instruction'].append(p['评论内容'])
        # data['input'].append(None)
        # data['output'].append(content)
pandas.DataFrame(data).to_csv('res/data.csv', encoding='utf-8', index=False)
