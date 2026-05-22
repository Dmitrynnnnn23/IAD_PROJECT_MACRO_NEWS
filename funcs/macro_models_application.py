import json
import math
import pandas as pd
import numpy as np
from macro_models import sign_to_text, is_lm_bp, is_mp_pc, ad_as, solow_hr, ramsey_model



### res = {...} - результат работы ллм по выделению сущностей из макроновостей

def res_from_text(r):
    if r == 'up':
        return 1
    elif r == 'down':
        return -1
    else:
        return 0


i = res_from_text(res['процентная ставка'])
y = res_from_text(res['ВВП'])
pi = res_from_text(res['инфляция'])
u = res_from_text(res['безработица'])
k = res_from_text(res['капитал'])
inv = res_from_text(res['инвестиции'])
q = res_from_text(res['производство'])
c = res_from_text(res['потребление'])
L = res_from_text(res['численность рабочей силы'])
s = res_from_text(res['сбережения'])
w = res_from_text(res['заработные платы'])
inc = res_from_text(res['доходы населения'])
e = res_from_text(res['валютный курс'])
im = res_from_text(res['импорт'])
ex = res_from_text(res['экспорт'])
g = res_from_text(res['государственные расходы'])
d = res_from_text(res['государственный долг'])
def_budget = res_from_text(res['дефицит бюджета'])

### немного макро логики для заполнения пропусков
if (y == 0) and (q == 0) and (inc!=0):
    y=inc

elif (y == 0) and (q != 0):
    y=q

net_ex = ex - im

if (net_ex == 0) and (e != 0):
    net_ex = e

if y == 0:
    dy = None
else:
    dy = y




#is_lm_bp
def make_is_lm_bp():

    return is_lm_bp(dy=dy, c_shock=c, i_shock=inv, g_shock=g, rate_shock=i, p_shock=pi, eps_shock=net_ex)

#is_mp_ps
def make_is_mp_pc():

    return is_mp_pc(dy=dy, c_shock=c, i_shock=inv, g_shock=g, eps_pi=q, rate_shock=i, p_shock=pi)

#ad_as
def make_ad_as():

    return ad_as(dy=dy, c_shock=c, i_shock=inv, g_shock=g, eps_as=q, rate_shock=i, p_shock=pi, l_shock=L, w_shock=w)

#solow_hr
def make_solow_hr():

    return solow_hr(dy=dy, s_shock=s, K_shock=k, L_shock=L)

#ramsey_model
def make_ramsey_model():

    return ramsey_model(Y_shock=y, K_shock=k, L_shock=L, C_shock=c, S_shock=s, G_shock=g, p_shock=pi, w_shock=w)





res_for_llm_interpretation = []
# Простраиваем алгорит выбора модели исходя из шоков, которые нужно объяснить
if w != 0:
    res_for_llm_interpretation.append(make_ad_as())
    res_for_llm_interpretation.append(make_ramsey_model())

elif L != 0:
    res_for_llm_interpretation.append(make_ad_as())
    res_for_llm_interpretation.append(make_solow_hr())

elif net_ex != 0:
    res_for_llm_interpretation.append(make_is_lm_bp())

elif pi != 0:
    res_for_llm_interpretation.append(make_is_mp_pc())
    res_for_llm_interpretation.append(make_ramsey_model())

elif s != 0:
    res_for_llm_interpretation.append(make_solow_hr())
    res_for_llm_interpretation.append(make_ramsey_model())

else:
    res_for_llm_interpretation.append(make_is_mp_pc())
    res_for_llm_interpretation.append(make_ramsey_model())


### res_for_llm_interpretation = то, что подаем в промпт ллм для объяснения
