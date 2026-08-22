# -*- coding: utf-8 -*-
"""追試2: dam_prio(母馬優先対象=母がクラブ在籍馬)の中身を割る。"""
import io, os, sys
import numpy as np, pandas as pd
from analyze5 import load, logit, design
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
pd.set_option('display.width',220)
BASE=os.path.dirname(os.path.abspath(__file__)); D=os.path.join(BASE,'..','..','data')
df=load(central_only=True); df['no_i']=pd.to_numeric(df['no'],errors='coerce')
rk=pd.read_csv(os.path.join(D,'dam_age_rank.csv'),encoding='utf-8-sig')
rk.columns=['year','no','dam','dam_born','dam_age_r','dam_season','t','rank','pool_filled']
m=df.merge(rk[['year','no','rank','pool_filled']],left_on=['year','no_i'],right_on=['year','no'],how='left',suffixes=('','_r'))
m['dam_prio']=m['rank'].notna().astype(int)
s=m[m['year'].between(2021,2024)].dropna(subset=['win_jra']).copy()

def reg(d,cols,ys=('win_jra','ret1'),tag=''):
    for y in ys:
        dd=d.dropna(subset=list(cols)+[y]); X,names=design(dd,list(cols)); r=logit(X,dd[y],names)
        print(f'  {tag}[{y}] n={len(dd)}'); print(r[~r['変数'].astype(str).str.startswith('年度')].to_string(index=False))

print('='*78); print('■ F. dam_prio の成績の中身'); print('='*78)
g=s.groupby('dam_prio')
print(pd.DataFrame({'頭数':g.size(),'勝上(中央)%':(g['win_jra'].mean()*100).round(1),
  '回収≥1 %':(g['ret1'].mean()*100).round(1),'回収中央値':g['ret'].median().round(3),
  '回収平均':g['ret'].mean().round(3),'回収75%':g['ret'].quantile(.75).round(3),
  '回収90%':g['ret'].quantile(.90).round(3),'重賞頭数':g['graded'].apply(lambda x:(x>0).sum()),
  '賞金中央値':g['prize'].median().round(0),'賞金平均':g['prize'].mean().round(0),
  '出走数中央値':g['starts'].median()}).to_string())
print()
print('外れ値の影響: 回収上位5頭を落として ret1 回帰')
cut=s.sort_values('ret',ascending=False).index[:5]
reg(s.drop(index=cut),['dam_prio'],ys=('ret1',),tag='上位5除外 ')
print('回収≥0.5 / ≥1.5 でも見る:')
for th in [0.5,1.5,2.0]:
    s[f'r{th}']=(s['ret']>=th).astype(float)
    a=s[s['dam_prio']==1][f'r{th}'].mean(); b=s[s['dam_prio']==0][f'r{th}'].mean()
    print(f'  回収≥{th}: 対象 {a:.1%}  非対象 {b:.1%}')
    reg(s,['dam_prio'],ys=(f'r{th}',),tag=f'  ')
print()
print('年度別 重賞出走馬:')
print(s.pivot_table(index='dam_prio',columns='year',values='graded',aggfunc=lambda x:(x>0).sum()).to_string())
print()
print('■ 2020年度を dam_prio=不明として扱った確認（dam_age_rankは2021〜のみ）')
print('  2020年度は判定不能なので除外している。除外前後で n:', len(m.dropna(subset=['win_jra'])), '→', len(s))
print()
print('='*78); print('■ G. dam_prio は「母の質」の代理か'); print('='*78)
print('母の年齢分布:'); print(s.groupby('dam_prio')['dam_age'].describe().round(2).to_string())
print('何番仔:'); s['nf_i']=pd.to_numeric(s['n_foals'],errors='coerce')
print(s.groupby('dam_prio')['nf_i'].describe().round(2).to_string())
print('  何番仔をコントロールした dam_prio:'); reg(s.dropna(subset=['nf_i']),['dam_prio','nf_i'])
print('  母年齢をコントロール:'); reg(s,['dam_prio','dam_age'])
print('  全部込み:'); s['price2539']=s['total_man'].between(2500,3999).astype(int)
s['w420']=(s['weight']>=420).astype(float); s.loc[s['weight'].isna(),'w420']=np.nan
reg(s.dropna(subset=['nf_i']),['dam_prio','male','price2539','w420','dam_age','nf_i'])

print(); print('='*78); print('■ H. 2024年度 中間発表の細目（母優枠D・最優先口数）'); print('='*78)
it=pd.read_csv(os.path.join(D,'carrot_interim.csv'),encoding='utf-8-sig')
it.columns=['year','no','name','kubun','total_app','dp_top','dp_gen','top_only']
i24=it[it['year']==2024].copy(); i24['D']=i24['dp_top'].fillna(0)+i24['dp_gen'].fillna(0)
d24=s[s['year']==2024].merge(i24[['no','total_app','top_only','D','kubun']].rename(columns={'no':'no_i'}),on='no_i',how='left')
h=d24.dropna(subset=['total_app']).copy()
print(f'  2024年度 中間掲載 {len(h)}頭')
for c,lab in [('total_app','総申込'),('top_only','最優先'),('D','母優枠D')]:
    hi=h[h[c]>=h[c].median()]; lo=h[h[c]<h[c].median()]
    print(f'  {lab} 中央値{h[c].median():.0f}: 上位 n={len(hi)} 勝上{hi["win_jra"].mean():.0%} 回収≥1 {hi["ret1"].mean():.0%} | '
          f'下位 n={len(lo)} 勝上{lo["win_jra"].mean():.0%} 回収≥1 {lo["ret1"].mean():.0%}')
print('  (単年・現3歳なので年度コントロール不可。参考値)')

print(); print('='*78); print('■ I. 満口データ'); print('='*78)
r1=pd.read_csv(os.path.join(D,'carrot_1ji_result.csv'),encoding='utf-8-sig')
print(r1.to_string())
print('→ 年度集計のみ。馬ごとの満口/残口は入っていないので検定不能。')
print('   ただし枠外ランクE(=一般出資枠で全口確定=実質残口)が代理になる。E の頭数:',
      '2021:3 2022:4 2023:9 2024:10（母馬優先対象馬のみ）')
