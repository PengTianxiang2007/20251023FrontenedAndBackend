from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ==================== 数据库配置（仅作展示，不实际连接）====================
# 注意：以下配置仅用于展示，实际不会在启动时连接数据库
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'database',
    'password': 'pdd070519',
    'database': 'database',
    'charset': 'utf8mb4'
}

# ==================== 基础数据 ====================

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
SHENGXIAO = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']

WUXING_TIANGAN = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
}

WUXING_DIZHI = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

SHICHEN_DIZHI = {
    23: '子', 1: '丑', 3: '寅', 5: '卯', 7: '辰', 9: '巳',
    11: '午', 13: '未', 15: '申', 17: '酉', 19: '戌', 21: '亥'
}

NAYIN_60 = [
    '海中金', '炉中火', '大林木', '路旁土', '剑锋金', '山头火',
    '涧下水', '城头土', '白蜡金', '杨柳木', '泉中水', '屋上土',
    '霹雳火', '松柏木', '长流水', '沙中金', '山下火', '平地木',
    '壁上土', '金箔金', '覆灯火', '天河水', '大驿土', '钗钏金',
    '桑柘木', '大溪水', '沙中土', '天上火', '石榴木', '大海水'
]

SHISHEN_NAMES = ['比肩', '劫财', '食神', '伤官', '偏财', '正财', '七杀', '正官', '偏印', '正印']

# ==================== 农历计算 ====================

def solar_to_lunar_simple(year, month, day):
    """简化的公历转农历"""
    base_date = datetime(1900, 1, 31)
    target_date = datetime(year, month, day)
    days_diff = (target_date - base_date).days
    
    lunar_year = 1900 + days_diff // 365
    lunar_month = ((days_diff % 365) // 30) + 1
    lunar_day = ((days_diff % 365) % 30) + 1
    
    if lunar_month > 12:
        lunar_month = 12
    if lunar_month < 1:
        lunar_month = 1
        
    return lunar_year, lunar_month, lunar_day

def get_year_gan_zhi(year):
    """计算年干支"""
    gan_index = (year - 4) % 10
    zhi_index = (year - 4) % 12
    return TIANGAN[gan_index] + DIZHI[zhi_index]

def get_month_gan_zhi(year, month, lunar_month):
    """计算月干支"""
    zhi_index = (lunar_month + 1) % 12
    year_gan_index = (year - 4) % 10
    gan_index = (year_gan_index * 2 + lunar_month) % 10
    return TIANGAN[gan_index] + DIZHI[zhi_index]

def get_day_gan_zhi(year, month, day):
    """计算日干支"""
    base_date = datetime(1900, 1, 1)
    target_date = datetime(year, month, day)
    days_diff = (target_date - base_date).days
    
    gan_index = (days_diff + 10) % 10
    zhi_index = (days_diff + 10) % 12
    
    return TIANGAN[gan_index] + DIZHI[zhi_index]

def get_hour_gan_zhi(day_gan, hour):
    """计算时干支"""
    hour_zhi = SHICHEN_DIZHI[hour]
    hour_zhi_index = DIZHI.index(hour_zhi)
    day_gan_index = TIANGAN.index(day_gan)
    hour_gan_index = (day_gan_index * 2 + hour_zhi_index) % 10
    return TIANGAN[hour_gan_index] + hour_zhi

# ==================== 纳音五行 ====================

def get_nayin(ganzhi):
    """获取纳音五行"""
    gan = ganzhi[0]
    zhi = ganzhi[1]
    gan_index = TIANGAN.index(gan)
    zhi_index = DIZHI.index(zhi)
    jiazi_index = (gan_index * 6 + zhi_index // 2) % 30
    return NAYIN_60[jiazi_index]

def get_nayin_description(nayin):
    """纳音五行解释"""
    descriptions = {
        '海中金': '大海深处之金,深藏不露,厚积薄发,需等待时机方能发光',
        '炉中火': '熔炉中的烈火,热情奔放,具有强大的改造能力',
        '大林木': '森林中的参天大树,根基深厚,能成大器',
        '路旁土': '道路两旁的泥土,平凡朴实,但承载万物',
        '剑锋金': '锋利的宝剑,锐不可当,具有果断决绝的性格',
        '山头火': '山顶的火焰,照亮四方,具有领导才能',
        '涧下水': '溪涧之水,清澈灵动,聪明机智',
        '城头土': '城墙的土,稳固可靠,有保护他人的责任感',
        '白蜡金': '白金之质,纯净高贵,追求完美',
        '杨柳木': '柳树之木,柔韧坚强,适应力强',
        '泉中水': '泉水清冽,生生不息,具有持续的活力',
        '屋上土': '屋顶之土,庇护众生,有奉献精神',
        '霹雳火': '雷电之火,爆发力强,做事干脆利落',
        '松柏木': '松柏长青,坚韧不拔,意志坚定',
        '长流水': '长江大河,奔流不息,事业长远',
        '沙中金': '沙中藏金,需经磨砺才能发光',
        '山下火': '山下炊烟,温暖人心,性情温和',
        '平地木': '平原树木,广泛普及,人缘极佳',
        '壁上土': '墙壁之土,坚固可靠,给人安全感',
        '金箔金': '金箔薄片,华丽精美,注重外表',
        '覆灯火': '灯火通明,照亮黑暗,有智慧之光',
        '天河水': '银河之水,浩瀚无边,志向远大',
        '大驿土': '驿站之土,善于沟通,交际广泛',
        '钗钏金': '首饰之金,精致美丽,品味高雅',
        '桑柘木': '桑树之木,养蚕织丝,勤劳致富',
        '大溪水': '溪流之水,灵活变通,善于应变',
        '沙中土': '沙土混合,踏实肯干,埋头苦干',
        '天上火': '天上烈日,光芒万丈,志向高远',
        '石榴木': '石榴之木,多子多福,家庭和睦',
        '大海水': '大海之水,包容万物,胸怀宽广'
    }
    return descriptions.get(nayin, '命格独特,需结合实际情况分析')

# ==================== 十神计算 ====================

def get_shishen(day_gan, other_gan):
    """计算十神关系"""
    day_index = TIANGAN.index(day_gan)
    other_index = TIANGAN.index(other_gan)
    day_yinyang = day_index % 2
    other_yinyang = other_index % 2
    day_wuxing_index = day_index // 2
    other_wuxing_index = other_index // 2
    diff = (other_wuxing_index - day_wuxing_index) % 5
    
    if diff == 0:
        return '比肩' if day_yinyang == other_yinyang else '劫财'
    elif diff == 1:
        return '食神' if day_yinyang == other_yinyang else '伤官'
    elif diff == 2:
        return '偏财' if day_yinyang == other_yinyang else '正财'
    elif diff == 3:
        return '七杀' if day_yinyang == other_yinyang else '正官'
    else:
        return '偏印' if day_yinyang == other_yinyang else '正印'

def analyze_shishen(bazi):
    """分析十神格局"""
    day_gan = bazi['day'][0]
    shishen_count = {name: 0 for name in SHISHEN_NAMES}
    
    for zhu in ['year', 'month', 'hour']:
        gan = bazi[zhu][0]
        shishen = get_shishen(day_gan, gan)
        shishen_count[shishen] += 1
    
    max_shishen = max(shishen_count, key=shishen_count.get)
    
    pattern_desc = {
        '比肩': '独立自主,做事有主见,但有时过于固执。适合创业或独当一面的工作',
        '劫财': '行动力强,敢于冒险,善于把握机会。注意与人合作时的利益分配',
        '食神': '温和善良,富有才华,享受生活。适合从事创意、艺术类工作',
        '伤官': '聪明机智,才华横溢,个性鲜明。适合创新性强的工作',
        '偏财': '善于经营,财运亨通,交际广泛。适合商业、金融类工作',
        '正财': '勤劳踏实,财富稳定,理财有道。适合稳定的财务管理工作',
        '七杀': '果断刚毅,具有威严,执行力强。适合管理、军警类工作',
        '正官': '正直守信,责任心强,适合仕途。宜从事公职或管理工作',
        '偏印': '聪明好学,多才多艺,思维独特。适合学术研究或技术工作',
        '正印': '仁慈厚道,学识渊博,贵人运强。适合教育、文化类工作'
    }
    
    return {
        'pattern': max_shishen + '格',
        'distribution': shishen_count,
        'description': pattern_desc.get(max_shishen, '命格独特')
    }

# ==================== 神煞计算 ====================

def get_shensha(bazi):
    """计算神煞"""
    day_zhi = bazi['day'][1]
    year_zhi = bazi['year'][1]
    shensha_list = []
    
    # 桃花
    taohua_map = {
        '子': '酉', '午': '卯', '卯': '子', '酉': '午',
        '寅': '午', '巳': '酉', '申': '子', '亥': '卯',
        '辰': '酉', '戌': '卯', '丑': '午', '未': '子'
    }
    if year_zhi in taohua_map:
        target = taohua_map[year_zhi]
        for zhu in ['year', 'month', 'day', 'hour']:
            if bazi[zhu][1] == target:
                shensha_list.append({
                    'name': '桃花星',
                    'description': '人缘佳,魅力强,异性缘旺',
                    'type': 'good'
                })
                break
    
    # 文昌
    wenchang_map = {
        '甲': '巳', '乙': '午', '丙': '申', '丁': '酉', '戊': '申',
        '己': '酉', '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯'
    }
    day_gan = bazi['day'][0]
    if day_gan in wenchang_map:
        target = wenchang_map[day_gan]
        for zhu in ['year', 'month', 'day', 'hour']:
            if bazi[zhu][1] == target:
                shensha_list.append({
                    'name': '文昌贵人',
                    'description': '聪明好学,考运佳,利学业',
                    'type': 'good'
                })
                break
    
    # 驿马
    yima_map = {
        '寅': '申', '午': '寅', '戌': '寅',
        '申': '寅', '子': '寅', '辰': '寅',
        '巳': '亥', '酉': '亥', '丑': '亥',
        '亥': '巳', '卯': '巳', '未': '巳'
    }
    if day_zhi in yima_map:
        target = yima_map[day_zhi]
        for zhu in ['year', 'month', 'day', 'hour']:
            if bazi[zhu][1] == target:
                shensha_list.append({
                    'name': '驿马星',
                    'description': '奔波劳碌,多动少静,利外出',
                    'type': 'good'
                })
                break
    
    # 华盖
    huagai_map = {
        '寅': '戌', '午': '戌', '戌': '戌',
        '申': '辰', '子': '辰', '辰': '辰',
        '巳': '丑', '酉': '丑', '丑': '丑',
        '亥': '未', '卯': '未', '未': '未'
    }
    if day_zhi in huagai_map:
        target = huagai_map[day_zhi]
        for zhu in ['year', 'month', 'day', 'hour']:
            if bazi[zhu][1] == target:
                shensha_list.append({
                    'name': '华盖星',
                    'description': '艺术天赋,孤高清傲,利修行',
                    'type': 'good'
                })
                break
    
    if len(shensha_list) < 2:
        shensha_list.append({
            'name': '天德贵人',
            'description': '逢凶化吉,遇难呈祥',
            'type': 'good'
        })
    
    return shensha_list[:4]

# ==================== 大运计算 ====================

def get_dayun(bazi, birth_year, is_male=True):
    """计算大运"""
    year_gan = bazi['year'][0]
    year_gan_index = TIANGAN.index(year_gan)
    is_yang_gan = year_gan_index % 2 == 0
    is_shun = (is_yang_gan and is_male) or (not is_yang_gan and not is_male)
    start_age = 8 if is_yang_gan else 7
    
    month_gan = bazi['month'][0]
    month_zhi = bazi['month'][1]
    month_gan_index = TIANGAN.index(month_gan)
    month_zhi_index = DIZHI.index(month_zhi)
    
    dayun_periods = []
    current_year = datetime.now().year
    current_age = current_year - birth_year
    
    for i in range(8):
        age_start = start_age + i * 10
        age_end = age_start + 9
        
        if is_shun:
            gan_index = (month_gan_index + i + 1) % 10
            zhi_index = (month_zhi_index + i + 1) % 12
        else:
            gan_index = (month_gan_index - i - 1) % 10
            zhi_index = (month_zhi_index - i - 1) % 12
        
        pillar = TIANGAN[gan_index] + DIZHI[zhi_index]
        is_current = age_start <= current_age <= age_end
        
        wuxing = WUXING_TIANGAN[TIANGAN[gan_index]]
        desc_map = {
            '金': '此运利财,决策果断,事业有成',
            '木': '此运生发,创意丰富,适合发展',
            '水': '此运智慧,灵活变通,贵人相助',
            '火': '此运热情,人际广泛,名声提升',
            '土': '此运稳健,脚踏实地,积累财富'
        }
        
        dayun_periods.append({
            'pillar': pillar,
            'start_age': age_start,
            'end_age': age_end,
            'is_current': is_current,
            'description': desc_map.get(wuxing, '运势平稳')
        })
        
        if i >= 2 and not any(p['is_current'] for p in dayun_periods):
            break
    
    return {
        'start_age': start_age,
        'periods': dayun_periods[:5]
    }

# ==================== 天乙贵人 ====================

def get_guiren(day_gan):
    """获取天乙贵人"""
    guiren_map = {
        '甲': '牛、羊', '戊': '牛、羊', '庚': '牛、羊',
        '乙': '鼠、猴', '己': '鼠、猴',
        '丙': '猪、鸡', '丁': '猪、鸡',
        '壬': '兔、蛇', '癸': '兔、蛇',
        '辛': '马、虎'
    }
    return guiren_map.get(day_gan, '龙、凤')

# ==================== 综合建议 ====================

def get_life_advice(bazi, wuxing_count, shishen, nayin):
    """生成人生建议"""
    advice_list = []
    
    min_element = min(wuxing_count, key=wuxing_count.get)
    if wuxing_count[min_element] == 0:
        element_advice = {
            '金': '多接触金属制品,从事决策性工作,培养果断性格',
            '木': '多接近大自然,培养创造力,发展艺术爱好',
            '水': '多读书学习,培养智慧,善用谋略思考',
            '火': '积极社交,保持热情,勇于表现自己',
            '土': '脚踏实地,注重积累,培养责任感'
        }
        advice_list.append(f'命中缺{min_element},建议{element_advice[min_element]}')
    
    pattern = shishen['pattern']
    if '食神' in pattern or '伤官' in pattern:
        advice_list.append('您富有创造力,适合从事艺术、设计、创意类工作,保持独特个性')
    elif '财' in pattern:
        advice_list.append('您有经商天赋,可大胆投资理财,但需注意风险控制,稳健为上')
    elif '官' in pattern or '杀' in pattern:
        advice_list.append('您有领导才能,适合管理工作或公职,注重规则与责任')
    elif '印' in pattern:
        advice_list.append('您好学多思,适合学术研究或教育工作,终身学习获益匪浅')
    elif '比劫' in pattern:
        advice_list.append('您独立性强,适合创业或独当一面,但需学会团队合作')
    
    if '金' in nayin:
        advice_list.append('纳音属金,宜从事金融、机械、技术行业,性格需磨练方显锋芒')
    elif '木' in nayin:
        advice_list.append('纳音属木,宜从事教育、文化、环保行业,保持生长向上的心态')
    elif '水' in nayin:
        advice_list.append('纳音属水,宜从事智力、流通、变动性工作,以柔克刚方为上策')
    elif '火' in nayin:
        advice_list.append('纳音属火,宜从事能源、餐饮、娱乐行业,热情是您最大的财富')
    elif '土' in nayin:
        advice_list.append('纳音属土,宜从事实业、房地产、农业,稳扎稳打必有收获')
    
    advice_list.append('命运掌握在自己手中,积极进取、为善最乐,方能趋吉避凶')
    
    return advice_list[:4]

# ==================== 五行统计 ====================

def count_wuxing(bazi):
    """统计五行"""
    wuxing_count = {'金': 0, '木': 0, '水': 0, '火': 0, '土': 0}
    
    for zhu in ['year', 'month', 'day', 'hour']:
        gan = bazi[zhu][0]
        zhi = bazi[zhu][1]
        wuxing_count[WUXING_TIANGAN[gan]] += 1
        wuxing_count[WUXING_DIZHI[zhi]] += 1
    
    return wuxing_count

# ==================== 主API ====================

@app.route('/calculate', methods=['POST'])
def calculate():
    """算命主接口"""
    try:
        data = request.json
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour = data.get('hour')
        
        if not all([year, month, day, hour is not None]):
            return jsonify({'error': '请提供完整的生辰信息'}), 400
        
        lunar_year, lunar_month, lunar_day = solar_to_lunar_simple(year, month, day)
        
        year_gz = get_year_gan_zhi(year)
        month_gz = get_month_gan_zhi(year, month, lunar_month)
        day_gz = get_day_gan_zhi(year, month, day)
        hour_gz = get_hour_gan_zhi(day_gz[0], hour)
        
        bazi = {
            'year': year_gz,
            'month': month_gz,
            'day': day_gz,
            'hour': hour_gz
        }
        
        bazi_str = f"{year_gz} {month_gz} {day_gz} {hour_gz}"
        wuxing_count = count_wuxing(bazi)
        nayin = get_nayin(year_gz)
        nayin_desc = get_nayin_description(nayin)
        shishen = analyze_shishen(bazi)
        shensha = get_shensha(bazi)
        dayun = get_dayun(bazi, year, is_male=True)
        guiren = get_guiren(day_gz[0])
        life_advice = get_life_advice(bazi, wuxing_count, shishen, nayin)
        
        result = {
            'bazi': bazi_str,
            'five_elements': wuxing_count,
            'nayin': nayin,
            'nayin_desc': nayin_desc,
            'shishen': shishen,
            'shensha': shensha,
            'dayun': dayun,
            'gui_ren': guiren,
            'life_advice': life_advice
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"计算错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'服务器计算错误: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': 'Flask服务运行正常'})

@app.route('/db-test', methods=['GET'])
def db_test():
    """数据库连接测试接口（演示用，不实际连接）"""
    try:
        # 这里不实际连接数据库，只返回配置信息作为展示
        return jsonify({
            'status': 'success',
            'message': '数据库配置已加载',
            'config': {
                'host': DB_CONFIG['host'],
                'port': DB_CONFIG['port'],
                'database': DB_CONFIG['database'],
                'user': DB_CONFIG['user']
            },
            'note': '数据库仅作展示，未实际连接'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'配置读取失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Flask服务启动中...")
    print("=" * 60)
    print(f"✓ 算命接口: http://134.175.18.101:5000/calculate")
    print(f"✓ 健康检查: http://134.175.18.101:5000/health")
    print(f"✓ 数据库测试: http://134.175.18.101:5000/db-test")
    print(f"✓ 数据库配置: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False)