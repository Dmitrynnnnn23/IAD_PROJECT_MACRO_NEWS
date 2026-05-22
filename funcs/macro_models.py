import json
import math



###-------------------------------------------------------------------------------------------------------------------------------------------------------------------
### IS-LM-BP
def sign_to_text(value, neutral_threshold=0.0000001):
    """Вспомогательная функция для форматирования знака изменения."""
    if abs(value) < neutral_threshold:
        return "Без изменений"
    return "Рост" if value > 0 else "Снижение"

def is_lm_bp(dy=None, di=None, c_shock=0, i_shock=0, g_shock=0, rate_shock=0, p_shock=0, eps_shock=0):
    """
    IS-LM-BP для малой открытой экономики с плавающим курсом

    Все шоки принимают только +1, -1 ИЛИ 0 (факт и направление шока)

    Параметры:
    dy, di — целевые изменения ВВП и ставки (если None, рассчитываются).
    rate_shock — Шок от решения ЦБ по номинальной ставке
    c_shock  — Шок потребления
    i_shock  — Шок инвестиций
    g_shock  — Шок государственных закупок
    p_shock  — Шок инфляции
    eps_shock — Шок экспорта
    """

    # Структурные параметры для российской экономики
    MPC = 0.6  # Предельная склонность к потреблению
    b = 2.0 # Чувствительность инвестиций к ставке
    k = 0.4  # Чувствительность спроса на деньги к доходу
    h = 2.0   # Чувствительность спроса на деньги к ставке (LM пологая)
    m = 0.5   # Предельная склонность к импорту
    delta = 0.3 # Чувствительность чистого экспорта к валютному курсу
    sigma = 1.0 # Мобильность капитала (BP крутая, LM положе BP)

    target_mode_dy = (dy is not None)
    target_mode_di = (di is not None)

    if not target_mode_dy and not target_mode_di:
        # Совокупный шок спроса
        demand_shock = c_shock + i_shock + g_shock + eps_shock

        # Шок реального предложения денег
        money_shock = -(h * rate_shock) - p_shock


        A11 = 1 - MPC + m
        A12 = b
        A13 = -delta
        A21 = k
        A22 = -h
        A23 = 0
        A31 = -m
        A32 = sigma
        A33 = delta

        B1 = demand_shock
        B2 = money_shock
        B3 = 0.0

        # Решение методом Крамера
        det_A = A11*(A22*A33 - A23*A32) - A12*(A21*A33 - A23*A31) + A13*(A21*A32 - A22*A31)
        if abs(det_A) < 0.00000001:
            return json.dumps({"Ошибка": "Матрица вырождена, модель не имеет решения"}, ensure_ascii=False)

        det_dy = B1*(A22*A33 - A23*A32) - A12*(B2*A33 - A23*B3) + A13*(B2*A32 - A22*B3)
        det_di = A11*(B2*A33 - A23*B3) - B1*(A21*A33 - A23*A31) + A13*(A21*B3 - B2*A31)
        det_de = A11*(A22*B3 - B2*A32) - A12*(A21*B3 - B2*A31) + B1*(A21*A32 - A22*A31)

        dy = det_dy / det_A
        di = det_di / det_A
        de = det_de / det_A

    else:
        if dy is None:
            dy = 0.0
        if di is None:
            di = 0.0

        if rate_shock != 0:
            di = float(rate_shock)

        de = (m * dy - sigma * di) / delta

    dc = c_shock + MPC * dy   # Изменение потребления
    di_comp = i_shock - b * di   # Изменение инвестиций
    dg = g_shock    # Изменение госзакупок
    dnx = delta * de - m * dy  # Изменение чистого экспорта

    results = {
        "Модель": "IS-LM-BP",
        "Основные макропоказатели": {
            "ВВП": sign_to_text(dy),
            "Ставка": sign_to_text(di),
            "Валютный курс": "Ослабление" if de > 0 else "Укрепление" if de < 0 else "Стабилен",
        },
        "Компоненты ВВП": {
            "Потребление": sign_to_text(dc),
            "Инвестиции": sign_to_text(di_comp),
            "Гос. закупки": sign_to_text(dg),
            "Чистый экспорт": sign_to_text(dnx)
        }
    }

    return json.dumps(results, ensure_ascii=False, indent=4)







###-------------------------------------------------------------------------------------------------------------------------------------------------------------------
### IS-MP-PC

def is_mp_pc(dy=None, di=None, c_shock=0, i_shock=0, g_shock=0, eps_pi=0, rate_shock=0, p_shock=0):
    """
    IS-MP-PC

    Все шоки принимают только +1, -1 или 0 (факт и направление шока).

    Параметры:
    dy, di - целевые изменения ВВП и ставки (если None, рассчитываются)
    rate_shock - Шок от решения ЦБ по номинальной ставке
    c_shock  - Шок потребления
    i_shock  - Шок инвестиций
    g_shock  - Шок государственных закупок
    eps_pi   - Шок предложения/инфляции издержек
    p_shock  - Шок уровня цен
    """

    # Параметры модели
    gamma = 0.4  # Чувствительность инфляции к разрыву выпуска (кривая Филлипса)
    alpha = 0.4 # Чувствительность выпуска к реальной ставке (трансмиссия)
    beta_pi = 2.0 # Реакция ЦБ на отклонение инфляции от цели (правило Тейлора)
    beta_y = 0.3  # Реакция ЦБ на разрыв выпуска (правило Тейлора)
    MPC = 0.6  # Предельная склонность к потреблению
    psi = 0.2 # Чувствительность инвестиций к реальной ставке

    target_mode_dy = (dy is not None)
    target_mode_di = (di is not None)
    target_mode = target_mode_dy or target_mode_di


    if not target_mode:
        # Шоки
        demand_shock = c_shock + i_shock + g_shock
        supply_shock = eps_pi + p_shock * 0.5
        effective_demand = demand_shock - alpha * rate_shock

        A = 1 + alpha * ((beta_pi - 1) * gamma + beta_y)
        B = effective_demand - alpha * (beta_pi - 1) * supply_shock - alpha * rate_shock

        dy = B / A
        dpi = gamma * dy + supply_shock
        di = beta_pi * dpi + beta_y * dy + rate_shock
        dr = di - dpi

    else:
        if dy is None:
            dy = 0.0
        if di is None:
            di = 0.0

        supply_shock = eps_pi + p_shock * 0.5

        if rate_shock != 0:
            di = float(rate_shock)

        if target_mode_dy and target_mode_di:
            dpi = (di - beta_y * dy - rate_shock) / beta_pi

        elif target_mode_dy:
            dpi = gamma * dy + supply_shock
            di = beta_pi * dpi + beta_y * dy + rate_shock

        elif target_mode_di:
            dy = (di - rate_shock - beta_pi * supply_shock) / (beta_pi * gamma + beta_y)
            dpi = gamma * dy + supply_shock

        dr = di - dpi


    dc = c_shock + MPC * dy    # Изменение потребления
    di_comp = i_shock - psi * (di - dpi) # Изменение инвестиций
    dg = g_shock    # Изменение госзакупок


    results = {
        "Модель": "IS-MP-PC",
        "Показатели": {
            "ВВП": sign_to_text(dy),
            "Инфляция": sign_to_text(dpi),
            "Номинальная процентная ставка": sign_to_text(di),
            "Реальная процентная ставка": sign_to_text(dr)
        },
        "Компоненты ВВП": {
            "Потребление": sign_to_text(dc),
            "Инвестиции": sign_to_text(di_comp),
            "Гос. закупки": sign_to_text(dg)
        },
        "Внешние шоки": {
            "Шок потребления": c_shock,
            "Шок инвестиций": i_shock,
            "Шок госзакупок": g_shock,
            "Шок предложения": eps_pi,
            "Шок цен": p_shock,
            "Шок ставки ЦБ": rate_shock
        }
    }

    return json.dumps(results, ensure_ascii=False, indent=4)








###-------------------------------------------------------------------------------------------------------------------------------------------------------------------
### AD-AS
def ad_as(dy=None, dp=None, c_shock=0, i_shock=0, g_shock=0, m_shock=0, eps_as=0, rate_shock=0, p_shock=0, y_pot_shock=0, l_shock=0, w_shock=0):
    """
    AD-AS


    Параметры:
    dy, dp - целевые изменения ВВП и уровня цен (если None, рассчитываются)
    c_shock  -  Шок потребления
    i_shock  -  Шок инвестиций
    g_shock  -  Шок государственных закупок
    m_shock-  Шок денежной массы
    eps_as  -  Шок предложения (технологический/ценовой)
    rate_shock- Шок номинальной ставки ЦБ
    p_shock  - Шок уровня цен (инфляционный)
    y_pot_shock -  Шок потенциального ВВП
    l_shock -  Шок численности рабочей силы
    w_shock -  Шок номинальной заработной платы
    """

    # Параметры AD
    mult_c = 0.5  # Мультипликатор потребления
    mult_i = 0.6   # Мультипликатор инвестиций
    mult_g = 0.7  # Мультипликатор госзакупок
    mult_m = 0.4   # Мультипликатор денежной массы

    # Параметры AS
    phi_p = 0.3   # Чувствительность спроса к уровню цен
    lambda_as = 0.6   # Чувствительность предложения к ценам

    # Параметры рынка труда и потенциала
    alpha_l = 0.7 # Эластичность выпуска по труду
    beta_w = 0.4 # Чувствительность зарплаты к уровню цен
    gamma_u = 0.3 # Чувствительность зарплаты к безработице
    delta_pot = 0.5 # Влияние потенциального ВВП на совокупное предложение

    target_mode_dy = (dy is not None)
    target_mode_dp = (dp is not None)
    target_mode = target_mode_dy or target_mode_dp

    if not target_mode:

        demand_shock = (mult_c * c_shock + mult_i * i_shock +
                       mult_g * g_shock + mult_m * m_shock)


        if rate_shock != 0:
            demand_shock -= mult_i * 0.5 * rate_shock + mult_c * 0.2 * rate_shock


        if p_shock != 0:
            demand_shock -= phi_p * p_shock

        supply_shock = eps_as

        if y_pot_shock != 0:
            supply_shock += delta_pot * y_pot_shock

        # Влияние рынка труда на AS
        labor_shock = 0
        if l_shock != 0:
            labor_shock += alpha_l * l_shock

        if w_shock != 0:
            labor_shock -= beta_w * w_shock
            supply_shock += beta_w * w_shock

        if p_shock != 0:
            supply_shock += beta_w * p_shock * 0.5

        det = 1 + phi_p * lambda_as
        dy = (demand_shock - phi_p * supply_shock) / det
        dp = lambda_as * dy + supply_shock

        d_real_money = m_shock - dp

        d_employment = dy / alpha_l if l_shock == 0 else dy / alpha_l + l_shock
        d_wages = beta_w * dp - gamma_u * (dy / alpha_l) + w_shock

        d_y_pot = y_pot_shock
        d_output_gap = dy - d_y_pot

    else:
        if dy is None:
            dy = 0.0
        if dp is None:
            dp = 0.0

        supply_shock = eps_as
        if y_pot_shock != 0:
            supply_shock += delta_pot * y_pot_shock
        if w_shock != 0:
            supply_shock += beta_w * w_shock
        if p_shock != 0:
            supply_shock += beta_w * p_shock * 0.5

        if target_mode_dy:
            dp = lambda_as * dy + supply_shock


        elif target_mode_dp:
            dy = (dp - supply_shock) / lambda_as



        d_real_money = m_shock - dp

        d_employment = dy / alpha_l if l_shock == 0 else dy / alpha_l + l_shock
        d_wages = beta_w * dp - gamma_u * (dy / alpha_l) + w_shock
        d_y_pot = y_pot_shock
        d_output_gap = dy - d_y_pot

    if 'd_output_gap' not in locals():
        d_output_gap = dy - y_pot_shock

    d_unemployment = -0.3 * d_output_gap

    results = {
        "Модель": "AD-AS",
        "Основные макропоказатели": {
            "ВВП": sign_to_text(dy),
            "Уровень цен": sign_to_text(dp),
            "Реальная денежная масса": sign_to_text(d_real_money),
            "Разрыв выпуска": sign_to_text(d_output_gap)
        },
        "Рынок труда": {
            "Занятость": sign_to_text(d_employment),
            "Номинальная зарплата": sign_to_text(d_wages),
            "Уровень безработицы": sign_to_text(d_unemployment)
        },
        "Потенциал экономики": {
            "Потенциальный ВВП": sign_to_text(d_y_pot if 'd_y_pot' in locals() else y_pot_shock),
            "Численность рабочей силы": sign_to_text(l_shock)
        },
        "Учитываемые шоки": {
            "Потребление": c_shock,
            "Инвестиции": i_shock,
            "Госзакупки": g_shock,
            "Денежная масса": m_shock,
            "Предложение": eps_as,
            "Ставка ЦБ": rate_shock,
            "Цены": p_shock,
            "Потенциальный ВВП": y_pot_shock,
            "Рабочая сила": l_shock,
            "Зарплата": w_shock
        }
    }
    return json.dumps(results, ensure_ascii=False, indent=4)






###-------------------------------------------------------------------------------------------------------------------------------------------------------------------
### Модель Солоу


def solow_hr(dy=None, dk=None, s_shock=0, K_shock=0, L_shock=0, A_shock=0, h_shock=0, delta_shock=0, n_shock=0, g_shock=0):
    """
    Модель Солоу с человеческим капиталом для российской экономики

    Все шоки принимают только +1, -1 или 0 (факт и направление шока)

    Параметры:
    dy, dk - целевые изменения ВВП и капиталовооружённости (если None, рассчитываются)
    s_shock - Шок нормы сбережения
    K_shock - Шок запаса физического капитала
    L_shock -Шок численности рабочей силы
    A_shock  -Шок совокупной факторной производительности/технологий
    h_shock  - Шок человеческого капитала/образования
    delta_shock- Шок нормы амортизации
    n_shock  - Шок темпа роста населения
    g_shock  - Шок темпа технического прогресса
    """
    alpha = 0.33
    beta = 0.35

    n_base = -0.005     # Базовый темп роста населения
    g_base = 0.02  # Базовый темп технического прогресса (2% в год)
    delta_base = 0.05 # Базовая норма амортизации (5%)
    s_k_base = 0.20    # Базовая норма сбережения в физический капитал (20% ВВП)
    s_h_base = 0.12  # Базовая доля инвестиций в человеческий капитал (12% ВВП)
    A_base = 1.0    # Базовая СФП
    convergence_speed = 0.05

    s_k = s_k_base + 0.05 * s_shock
    s_k = max(0.01, min(0.50, s_k))

    s_h = s_h_base + 0.03 * h_shock
    s_h = max(0.01, min(0.30, s_h))

    n = n_base + 0.003 * n_shock
    g = g_base + 0.005 * g_shock
    delta = delta_base + 0.01 * delta_shock
    A = A_base * (1 + 0.02 * A_shock)

    h_effective = math.exp(0.15 * (s_h * 100)) * (1 + 0.03 * h_shock)

    target_mode_dy = (dy is not None)
    target_mode_dk = (dk is not None)
    target_mode = target_mode_dy or target_mode_dk

    if not target_mode:
        denominator = n + g + delta
        if denominator <= 0:
            denominator = 0.001

        k_star = math.pow(s_k / denominator, 1 / (1 - alpha - beta))
        y_star = A * math.pow(k_star, alpha) * math.pow(h_effective, beta)
        y_per_capita = y_star * A
        if K_shock != 0 or L_shock != 0:
            current_k = k_star * (1 + 0.1 * (K_shock - L_shock))
        else:
            current_k = k_star

        k_gap = current_k - k_star

        if k_gap < -0.001:
            growth_dynamics = "Ускорение роста (капитал ниже равновесного уровня)"
            dy_short = convergence_speed * abs(k_gap) * y_star
        elif k_gap > 0.001:

            growth_dynamics = "Замедление роста (капитал выше равновесного уровня)"
            dy_short = -convergence_speed * abs(k_gap) * y_star
        else:
            growth_dynamics = "Устойчивое состояние (стабильный рост)"
            dy_short = 0

        dy_long = y_per_capita - (A_base * math.pow(
            math.pow(s_k_base / (n_base + g_base + delta_base), 1/(1-alpha-beta)),
            alpha) * math.pow(math.exp(0.15 * (s_h_base * 100)), beta))

        dy_total = dy_long + dy_short

        w = (1 - alpha - beta) * y_per_capita
        dw = w - (1 - alpha - beta) * A_base * math.pow(
            math.pow(s_k_base / (n_base + g_base + delta_base), 1/(1-alpha-beta)),
            alpha) * math.pow(math.exp(0.15 * (s_h_base * 100)), beta)
        dk_total = current_k - k_star

    else:
        if dy is None:
            dy = 0.0
        if dk is None:
            dk = 0.0


        y_target = A_base * (1 + dy * 0.01)
        k_needed = math.pow(y_target / (A * math.pow(h_effective, beta)), 1/alpha)

        denominator = n + g + delta
        s_k_needed = k_needed * denominator
        k_star = math.pow(s_k / denominator, 1 / (1 - alpha - beta))
        y_star = A * math.pow(k_star, alpha) * math.pow(h_effective, beta)

        dy_long = y_target - y_star
        dy_short = 0
        growth_dynamics = "Целевая траектория"
        dy_total = dy_long

        # Заработная плата
        w = (1 - alpha - beta) * y_target
        dw = w - (1 - alpha - beta) * y_star

        k_gap = k_needed - k_star
        dk_total = k_gap



    dp = -dy_total * 0.5

    real_wage_change = dw - dp


    results = {
        "Модель": "Солоу с человеческим капиталом",
        "Долгосрочные показатели": {
            "ВВП на душу населения": sign_to_text(dy_total),
            "Капиталовооружённость": sign_to_text(dk_total),
            "Устойчивый уровень ВВП": sign_to_text(y_star),
            "Устойчивая капиталовооружённость": sign_to_text(k_star)
        },
        "Краткосрочная динамика": {
            "Направление изменения ВВП": sign_to_text(dy_short),
            "Характер роста": growth_dynamics,
            "Разрыв капиталовооружённости": sign_to_text(k_gap if 'k_gap' in locals() else dk_total)
        },
        "Рынок труда и доходы": {
            "Реальная заработная плата": sign_to_text(real_wage_change),
            "Номинальная заработная плата": sign_to_text(dw)
        },
        "Внешние шоки": {
            "Сбережения": sign_to_text(s_shock),
            "Капитал": sign_to_text(K_shock),
            "Рабочая сила": sign_to_text(L_shock),
            "Технологии": sign_to_text(A_shock),
            "Человеческий капитал": sign_to_text(h_shock),
            "Амортизация": sign_to_text(delta_shock),
            "Демография": sign_to_text(n_shock),
            "Техпрогресс": sign_to_text(g_shock)
        }
    }

    return json.dumps(results, ensure_ascii=False, indent=4)



###-------------------------------------------------------------------------------------------------------------------------------------------------------------------
### Модель Рамсея


def ramsey_model(dy=None, dr=None, Y_shock=0, K_shock=0, L_shock=0, C_shock=0, S_shock=0, G_shock=0, A_shock=0, p_shock=0, w_shock=0, tau_shock=0):
    """
    Модель Рамсея

    Параметры:
    dy, dr -  целевые изменения ВВП и реальной процентной ставки (если None, рассчитываются)
    Y_shock- Шок выпуска/ВВП
    K_shock- Шок запаса капитала
    L_shock - Шок численности рабочей силы
    C_shock - Шок потребления
    S_shock - Шок сбережений
    G_shock -Шок государственных закупок
    A_shock - Шок совокупной факторной производительности
    p_shock - Шок уровня цен
    w_shock - Шок номинальной заработной платы
    tau_shock-Шок налоговой нагрузки
    """

    alpha = 0.33  # Доля капитала в ВВП
    beta = 0.6 # Субъективный дисконт-фактор (терпение домохозяйств)
    delta = 0.05 # Норма амортизации капитала
    theta = 1.5 # Эластичность межвременного замещения в потреблении
    rho = -math.log(beta) # Норма межвременных предпочтений

    # Параметры фискальной политики
    tau = 0.20  # Базовая налоговая нагрузка
    gy_ratio = 0.30   # Доля госрасходов в ВВП


    patience_signal = S_shock - C_shock
    effective_beta = beta + 0.02 * patience_signal
    effective_beta = max(0.90, min(0.995, effective_beta))
    effective_rho = -math.log(effective_beta)

    tau = tau + 0.03 * tau_shock
    tau = max(0.10, min(0.35, tau))

    A_effective = 1.0 + 0.03 * A_shock

    target_mode_dy = (dy is not None)
    target_mode_dr = (dr is not None)
    target_mode = target_mode_dy or target_mode_dr

    if not target_mode:

        target_r = effective_rho
        mpk_target = target_r + delta
        if mpk_target <= 0:
            mpk_target = 0.001

        k_star = (alpha * A_effective / mpk_target) ** (1 / (1 - alpha))

        if K_shock != 0 or L_shock != 0:
            k_current = k_star * (1 + 0.15 * K_shock - 0.10 * L_shock)
        else:
            k_current = k_star

        y_star = A_effective * (k_star ** alpha)

        y_current = A_effective * (k_current ** alpha)
        if Y_shock != 0:
            y_current *= (1 + 0.05 * Y_shock)

        capital_gap = k_star - k_current

        if capital_gap > 0.001:
            dy_direction = 1
            growth_stage = "Рост (экономика ниже устойчивого состояния)"
        elif capital_gap < -0.001:
            dy_direction = -1
            growth_stage = "Замедление (экономика выше устойчивого состояния)"
        else:
            dy_direction = 0
            growth_stage = "Устойчивое состояние (сбалансированный рост)"

        mpk_current = alpha * A_effective * (k_current ** (alpha - 1))
        r_current = mpk_current - delta
        r_direction = 1 if r_current > target_r else (-1 if r_current < target_r else 0)

        i_direction = 1 if capital_gap > 0 else (-1 if capital_gap < 0 else 0)

        if G_shock > 0:
            c_direction = -1 if capital_gap >= 0 else (1 if capital_gap < 0 else 0)
        else:
            c_direction = 1 if capital_gap > 0 else (-1 if capital_gap < 0 else 0)

        mpl_current = (1 - alpha) * A_effective * (k_current ** alpha)
        mpl_star = (1 - alpha) * A_effective * (k_star ** alpha)
        w_direction = 1 if mpl_current > mpl_star else (-1 if mpl_current < mpl_star else 0)

        if w_shock != 0:
            w_direction = w_shock

        p_direction = -dy_direction if p_shock == 0 else p_shock
        crowding_out = "Да (госрасходы вытесняют частные инвестиции)" if G_shock > 0 else "Нет"

        y_potential = y_star
        output_gap = (y_current - y_potential) / y_potential

    else:
        if dy is None:
            dy = 0.0
        if dr is None:
            dr = 0.0

        target_r = effective_rho + dr * 0.01

        mpk_target = target_r + delta
        k_star = (alpha * A_effective / mpk_target) ** (1 / (1 - alpha))

        y_star = A_effective * (k_star ** alpha)
        y_target = y_star * (1 + dy * 0.01)

        k_needed = (y_target / A_effective) ** (1 / alpha)

        s_needed = (delta * k_needed) / y_target

        capital_gap = k_needed - k_star
        dy_direction = dy
        growth_stage = "Целевая траектория"
        r_direction = dr
        i_direction = 1 if capital_gap > 0 else (-1 if capital_gap < 0 else 0)
        c_direction = -i_direction
        w_direction = dy_direction
        p_direction = -dy_direction

        k_current = k_star
        y_current = y_star
        mpl_current = (1 - alpha) * A_effective * (k_current ** alpha)
        r_current = target_r
        output_gap = (y_target - y_star) / y_star
        crowding_out = "Зависит от структуры политики"

        if target_mode_dr and not target_mode_dy:
            y_target = y_star
            dy_direction = 0

    results = {
        "Модель": "Рамсея",
        "Долгосрочное равновесие": {
            "Целевая капиталовооружённость (k*)": k_star,
            "Потенциальный ВВП (y*)": y_star,
            "Равновесная реальная ставка (r*)": target_r,
            "Норма межвременных предпочтений (ρ)": effective_rho
        },
        "Краткосрочный период": {
            "ВВП": sign_to_text(dy_direction),
            "Реальная процентная ставка": sign_to_text(r_direction),
            "Инвестиции": sign_to_text(i_direction),
            "Потребление домохозяйств": sign_to_text(c_direction),
            "Реальная заработная плата": sign_to_text(w_direction),
            "Уровень цен": sign_to_text(p_direction)
        },
        "Макроэкономические индикаторы": {
            "Разрыв выпуска": output_gap,
            "Эффект вытеснения": crowding_out,
            "Стадия делового цикла": growth_stage,
            "Терпение домохозяйств": "Высокое (больше сберегают)" if patience_signal > 0 else "Низкое (больше потребляют)" if patience_signal < 0 else "Нейтральное"
        }
    }

    return json.dumps(results, ensure_ascii=False, indent=4)
