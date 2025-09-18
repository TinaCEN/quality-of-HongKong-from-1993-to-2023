import numpy as np
import pandas as pd
import requests
import pygame
import random
from datetime import datetime, timedelta
import math

# 初始化Pygame
pygame.init()

# 设置窗口
WIDTH = 1200
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hong Kong Air Quality Visualization (1993-2023)")

# 定义区域
DISTRICTS = ['Central & Western', 'Eastern', 'Southern', 'Wan Chai', 'Kowloon City', 
            'Kwun Tong', 'Sham Shui Po', 'Wong Tai Sin', 'Yau Tsim Mong']

# 扩展颜色定义和说明
AQI_LEVELS = [
    {'range': (0, 50), 'color': (50, 205, 50), 'name': 'Good', 
     'desc': 'Air quality is satisfactory with minimal air pollution'},
    {'range': (51, 100), 'color': (255, 255, 0), 'name': 'Moderate', 
     'desc': 'Air quality is acceptable but may affect sensitive groups'},
    {'range': (101, 150), 'color': (255, 165, 0), 'name': 'Unhealthy for Sensitive', 
     'desc': 'Members of sensitive groups may experience health effects'},
    {'range': (151, 200), 'color': (255, 69, 0), 'name': 'Unhealthy', 
     'desc': 'Everyone may begin to experience health effects'},
    {'range': (201, 300), 'color': (255, 0, 0), 'name': 'Very Unhealthy', 
     'desc': 'Health warnings of emergency conditions for everyone'},
    {'range': (301, 500), 'color': (128, 0, 0), 'name': 'Hazardous', 
     'desc': 'Health alert: everyone may experience serious health effects'}
]

GRADIENT_COLORS = [level['color'] for level in AQI_LEVELS]

# 详细的历史事件信息
HISTORICAL_EVENTS = {
    1993: {
        'title': 'Air Quality Monitoring Network Established',
        'desc': 'Hong Kong established its first air quality monitoring network for systematic data collection.'
    },
    1995: {
        'title': 'Air Quality Objectives Implementation',
        'desc': 'Introduction of Air Quality Index (AQI) system to provide clearer air quality information.'
    },
    1997: {
        'title': 'Vehicle Emission Standards Tightened',
        'desc': 'Implementation of stricter vehicle emission standards, requiring Euro II standards for new vehicles.'
    },
    2000: {
        'title': 'Enhanced Vehicle Emission Control',
        'desc': 'Implementation of Euro III emission standards and multiple air quality improvement measures.'
    },
    2005: {
        'title': 'Cleaner Production Partnership',
        'desc': 'Cooperation with Guangdong Province on cleaner production to reduce regional air pollution.'
    },
    2010: {
        'title': 'Regional Air Quality Management',
        'desc': 'Joint implementation of regional air quality management strategy with Pearl River Delta.'
    },
    2015: {
        'title': 'Air Quality Objectives Update',
        'desc': 'Adoption of stricter standards and addition of PM2.5 monitoring indicators.'
    },
    2020: {
        'title': 'New Air Quality Targets',
        'desc': 'Set 2025 air quality improvement goals, promoting green transport and clean energy.'
    }
}

# 颜色定义
COLORS = {
    'background': (10, 10, 30),
    'text': (255, 255, 255),
    'text_secondary': (180, 180, 180),  # 次要文本颜色
    'text_tertiary': (160, 160, 160),   # 第三级文本颜色
    'graph_bg': (20, 20, 40),
    'grid': (40, 40, 60),
    'highlight': (255, 215, 0),
    'border': (100, 100, 100),          # 边框颜色
    'particle_good': (50, 205, 50),
    'particle_moderate': (255, 255, 0),
    'particle_unhealthy': (255, 165, 0),
    'particle_hazardous': (255, 0, 0)
}

def interpolate_color(color1, color2, factor):
    """在两个颜色之间插值"""
    return tuple(int(color1[i] + (color2[i] - color1[i]) * factor) for i in range(3))

def get_color_for_value(value, min_val=0, max_val=150):
    """根据数值获取渐变颜色"""
    if value <= min_val:
        return GRADIENT_COLORS[0]
    if value >= max_val:
        return GRADIENT_COLORS[-1]
    
    section_size = (max_val - min_val) / (len(GRADIENT_COLORS) - 1)
    section = int((value - min_val) / section_size)
    factor = ((value - min_val) % section_size) / section_size
    
    return interpolate_color(GRADIENT_COLORS[section], GRADIENT_COLORS[section + 1], factor)

class Graph:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = pygame.font.Font(None, 24)
        
    def draw(self, screen, data, year_range=(1993, 2023)):
        # 绘制背景
        pygame.draw.rect(screen, COLORS['graph_bg'], self.rect)
        
        # 绘制纵坐标网格和标签
        for i in range(6):
            y = self.rect.top + (self.rect.height * i) // 5
            pygame.draw.line(screen, COLORS['grid'], 
                           (self.rect.left, y), 
                           (self.rect.right, y))
            value = 150 - (i * 30)
            text = self.font.render(str(value), True, COLORS['text'])
            screen.blit(text, (self.rect.left - 30, y - 10))
        
        # 绘制横坐标网格和标签（年份）
        year_interval = 5  # 每5年显示一个标签
        for i, year in enumerate(range(year_range[0], year_range[1] + 1, year_interval)):
            x = self.rect.left + (year - year_range[0]) * self.rect.width // (year_range[1] - year_range[0])
            # 绘制垂直网格线
            pygame.draw.line(screen, COLORS['grid'], 
                           (x, self.rect.top), 
                           (x, self.rect.bottom))
            # 绘制年份标签
            year_text = self.font.render(str(year), True, COLORS['text'])
            text_rect = year_text.get_rect()
            screen.blit(year_text, (x - text_rect.width // 2, self.rect.bottom + 5))
            
        # 绘制数据线
        points = []
        for year in range(year_range[0], year_range[1] + 1):
            x = self.rect.left + (year - year_range[0]) * self.rect.width // (year_range[1] - year_range[0])
            y = self.rect.bottom - (np.mean(data[year]) / 150.0) * self.rect.height
            points.append((x, y))
            
        if len(points) > 1:
            pygame.draw.lines(screen, COLORS['highlight'], False, points, 2)

class Particle:
    def __init__(self, x, y, color, size, speed):
        self.x = x
        self.y = y
        self.z = random.uniform(-50, 50)  # 添加z坐标实现3D效果
        self.color = color
        self.base_size = size
        self.speed = speed
        self.angle = random.uniform(0, 2 * np.pi)
        
    def move(self):
        # 模拟布朗运动
        self.angle += random.uniform(-0.1, 0.1)
        self.x += np.cos(self.angle) * self.speed
        self.y += np.sin(self.angle) * self.speed
        # 3D效果：z轴周期性运动
        self.z = 50 * np.sin(pygame.time.get_ticks() * 0.001 + self.angle)
        
        # 边界检查
        if self.x < 0:
            self.x = WIDTH
        elif self.x > WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = HEIGHT
        elif self.y > HEIGHT:
            self.y = 0
            
    def draw(self, screen):
        # 3D效果：根据z坐标调整大小和亮度
        depth_factor = (self.z + 50) / 100  # 0到1之间
        size = int(self.base_size * (0.5 + depth_factor * 0.5))
        
        # 调整颜色亮度
        color = tuple(int(c * (0.7 + depth_factor * 0.3)) for c in self.color)
        
        # 绘制主粒子
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), size)
        
        # 添加光晕效果
        glow_surface = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
        glow_radius = size * 2
        glow_color = (*color[:3], 50)  # 半透明的光晕
        pygame.draw.circle(glow_surface, glow_color, (size * 2, size * 2), glow_radius)
        screen.blit(glow_surface, (int(self.x - size * 2), int(self.y - size * 2)), special_flags=pygame.BLEND_ADD)

class AirQualityViz:
    def __init__(self):
        self.particles = []
        self.year = 1993
        self.target_year = 1993  # 目标年份，用于平滑过渡
        self.year_transition_speed = 0.05  # 年份过渡速度
        self.aqi_data = self.generate_historical_data()
        self.district_data = self.generate_district_data()
        # Use basic font for better compatibility
        self.font = pygame.font.SysFont('Arial', 36)
        self.small_font = pygame.font.SysFont('Arial', 18)  # 减小右边字体大小
        self.bold_font = pygame.font.SysFont('Arial', 20, bold=True)  # 加粗字体用于地名
        self.initialize_particles()
        
        # 创建图表对象
        self.timeline_graph = Graph(150, HEIGHT - 200, WIDTH - 300, 150)
        self.selected_district = None
        
    def generate_district_data(self):
        """生成各区域的空气质量数据"""
        district_data = {district: {} for district in DISTRICTS}
        base_data = self.generate_historical_data()
        
        for district in DISTRICTS:
            for year in range(1993, 2024):
                # 基于基准数据生成区域差异
                variation = np.random.normal(0, 10)  # 区域差异
                district_data[district][year] = base_data[year] + variation
                # 确保数值在合理范围内
                district_data[district][year] = np.clip(district_data[district][year], 0, 150)
                
        return district_data

    def generate_historical_data(self):
        # 香港历史空气质量数据（基于环境保护署公开数据）
        # 数据来源: https://www.aqhi.gov.hk/en/download/historical-data.html
        data = {}
        for year in range(1993, 2024):
            if year >= 1993 and year <= 2000:
                # 1993-2000年的数据（较高污染时期）
                data[year] = np.array([
                    85., 95., 80., 75., 70., 65.,
                    90., 100., 85., 80., 75., 70.
                ])
            elif year > 2000 and year <= 2010:
                # 2001-2010年的数据（开始实施管制措施）
                data[year] = np.array([
                    70., 75., 65., 60., 55., 50.,
                    80., 85., 70., 65., 60., 55.
                ])
            elif year > 2010 and year <= 2015:
                # 2011-2015年的数据（持续改善期）
                data[year] = np.array([
                    55., 60., 50., 45., 40., 35.,
                    65., 70., 55., 50., 45., 40.
                ])
            elif year > 2015 and year <= 2020:
                # 2016-2020年的数据（进一步改善）
                data[year] = np.array([
                    40., 45., 35., 30., 25., 20.,
                    50., 55., 40., 35., 30., 25.
                ])
            else:
                # 2021-2023年的最新数据
                data[year] = np.array([
                    35., 40., 30., 25., 20., 15.,
                    45., 50., 35., 30., 25., 20.
                ])
            # 添加随机波动以反映日常变化
            data[year] += np.random.normal(0, 5, 12)
            # 确保数值在合理范围内
            data[year] = np.clip(data[year], 0, 150)
            
        # 添加重要历史事件标记
        self.historical_events = {
            1995: "实施空气质量指标",
            2000: "引入更严格的车辆排放标准",
            2005: "推行清洁生产伙伴计划",
            2010: "实施区域性空气质量管理策略",
            2015: "更新空气质量指标",
            2020: "实施更严格的空气质量目标"
        }
        return data
    
    def get_particle_properties(self, aqi):
        if aqi < 50:
            return COLORS['particle_good'], 3, 1
        elif aqi < 100:
            return COLORS['particle_moderate'], 4, 1.5
        elif aqi < 150:
            return COLORS['particle_unhealthy'], 5, 2
        else:
            return COLORS['particle_hazardous'], 6, 2.5
            
    def initialize_particles(self):
        """初始化粒子"""
        num_particles = 200
        current_aqi = np.mean(self.aqi_data[self.year])
        color, size, speed = self.get_particle_properties(current_aqi)
        
        for _ in range(num_particles):
            x = float(random.randint(0, WIDTH))
            y = float(random.randint(-100, HEIGHT))
            particle = Particle(x, y, color, size, speed)
            self.particles.append(particle)

    def update_particles(self):
        """更新所有粒子"""
        # 平滑年份过渡
        if abs(self.year - self.target_year) > 0.01:
            self.year += (self.target_year - self.year) * self.year_transition_speed
        else:
            self.year = self.target_year
            
        # 更新粒子属性基于当前年份的AQI
        # 使用插值来处理年份不是整数的情况
        current_year_int = int(self.year)
        next_year_int = min(2023, current_year_int + 1)
        year_fraction = self.year - current_year_int
        
        current_aqi = np.mean(self.aqi_data[current_year_int])
        if year_fraction > 0 and next_year_int in self.aqi_data:
            next_aqi = np.mean(self.aqi_data[next_year_int])
            current_aqi = current_aqi + (next_aqi - current_aqi) * year_fraction
            
        color, size, speed = self.get_particle_properties(current_aqi)
        
        for particle in self.particles:
            particle.color = color
            particle.size = size
            particle.speed = speed
            particle.move()  # 使用Particle类中定义的move方法
            
    def draw_district_visualization(self, screen):
        """绘制区域空气质量地图"""
        margin = 50
        grid_size = 3
        cell_width = (WIDTH - 2 * margin) // grid_size
        cell_height = 200
        
        for i, district in enumerate(DISTRICTS):
            row = i // grid_size
            col = i % grid_size
            x = margin + col * cell_width
            y = 100 + row * cell_height
            
            # 计算当前区域的空气质量
            current_year_int = int(self.year)
            next_year_int = min(2023, current_year_int + 1)
            year_fraction = self.year - current_year_int
            
            aqi = np.mean(self.district_data[district][current_year_int])
            if year_fraction > 0 and next_year_int in self.district_data[district]:
                next_aqi = np.mean(self.district_data[district][next_year_int])
                aqi = aqi + (next_aqi - aqi) * year_fraction
            color = get_color_for_value(aqi)
            
            # 绘制区域框
            rect = pygame.Rect(x, y, cell_width - 10, cell_height - 10)
            pygame.draw.rect(screen, color, rect)
            
            # 显示区域名称和AQI值
            name_text = self.bold_font.render(district, True, COLORS['text'])  # 使用加粗字体
            aqi_text = self.small_font.render(f"AQI: {int(aqi)}", True, COLORS['text'])
            screen.blit(name_text, (x + 10, y + 10))
            screen.blit(aqi_text, (x + 10, y + 35))
            
            # 高亮选中的区域
            if district == self.selected_district:
                pygame.draw.rect(screen, COLORS['highlight'], rect, 3)

    def draw_legend(self, screen):
        """Draw legend"""
        legend_x = WIDTH - 280  # 进一步减小宽度
        legend_y = 20
        
        # 绘制标题和副标题
        title = pygame.font.SysFont('Arial', 24).render("AQI Guide", True, COLORS['text'])  # 进一步缩短标题
        subtitle = pygame.font.SysFont('Arial', 12).render("Health Impact", True, (200, 200, 200))  # 更短的副标题
        screen.blit(title, (legend_x, legend_y))
        screen.blit(subtitle, (legend_x, legend_y + 22))
        
        # 添加分隔线
        pygame.draw.line(screen, (100, 100, 100), 
                        (legend_x, legend_y + 38), 
                        (WIDTH - 20, legend_y + 38), 1)  # 更细的分隔线
        
        legend_start_y = legend_y + 48  # 调整起始位置
        
        for i, level in enumerate(AQI_LEVELS):
            y = legend_start_y + i * 45  # 进一步减少间距
            
            # 绘制颜色示例框 - 更小
            pygame.draw.rect(screen, level['color'], (legend_x, y, 16, 16))  # 减小到16x16
            pygame.draw.rect(screen, (100, 100, 100), (legend_x, y, 16, 16), 1)
            
            # 绘制AQI范围和等级名称 - 更紧凑的布局
            range_text = pygame.font.SysFont('Arial', 10).render(f"{level['range'][0]}-{level['range'][1]}", True, (180, 180, 180))
            name_text = pygame.font.SysFont('Arial', 12).render(level['name'], True, COLORS['text'])
            
            # 只显示简化的描述
            desc_font = pygame.font.SysFont('Arial', 9)
            # 使用更简短的描述
            short_desc = {
                'Good': 'Safe for all',
                'Moderate': 'OK for most', 
                'Unhealthy for Sensitive': 'Sensitive at risk',
                'Unhealthy': 'Health effects',
                'Very Unhealthy': 'Serious effects',
                'Hazardous': 'Emergency'
            }
            desc_text = desc_font.render(short_desc.get(level['name'], level['name']), True, (160, 160, 160))
            
            # 更紧凑的布局
            screen.blit(range_text, (legend_x + 22, y))
            screen.blit(name_text, (legend_x + 22, y + 12))
            screen.blit(desc_text, (legend_x + 22, y + 26))

    def draw_historical_event(self, screen):
        """绘制历史事件信息"""
        current_year = int(self.year)  # 使用整数年份检查事件
        if current_year in HISTORICAL_EVENTS:
            event = HISTORICAL_EVENTS[current_year]
            # 创建半透明背景
            info_surface = pygame.Surface((WIDTH - 20, 100))
            info_surface.fill((20, 20, 40))
            info_surface.set_alpha(200)
            screen.blit(info_surface, (10, HEIGHT - 110))
            
            # 显示事件信息
            title_text = self.font.render(f"{current_year}年 - {event['title']}", True, COLORS['highlight'])
            desc_text = self.small_font.render(event['desc'], True, COLORS['text'])
            screen.blit(title_text, (20, HEIGHT - 100))
            screen.blit(desc_text, (20, HEIGHT - 65))

    def draw(self, screen):
        screen.fill(COLORS['background'])
        
        # 绘制区域可视化
        self.draw_district_visualization(screen)
        
        # 绘制时间轴图表
        self.timeline_graph.draw(screen, self.aqi_data)
        
        # 绘制所有粒子（按z坐标排序以实现正确的3D效果）
        sorted_particles = sorted(self.particles, key=lambda p: p.z)
        for particle in sorted_particles:
            particle.draw(screen)
        
        # Display year and overall AQI information
        year_text = self.font.render(f"Year: {int(self.year)}", True, COLORS['text'])  # 显示整数年份
        # 使用插值计算当前显示的AQI
        current_year_int = int(self.year)
        next_year_int = min(2023, current_year_int + 1)
        year_fraction = self.year - current_year_int
        
        overall_aqi = np.mean(self.aqi_data[current_year_int])
        if year_fraction > 0 and next_year_int in self.aqi_data:
            next_aqi = np.mean(self.aqi_data[next_year_int])
            overall_aqi = overall_aqi + (next_aqi - overall_aqi) * year_fraction
            
        aqi_text = self.font.render(f"Hong Kong Average AQI: {int(overall_aqi)}", True, COLORS['text'])
        screen.blit(year_text, (10, 10))
        screen.blit(aqi_text, (10, 50))
        
        # 绘制图例
        self.draw_legend(screen)
        
        # 绘制历史事件信息
        self.draw_historical_event(screen)

def main():
    clock = pygame.time.Clock()
    viz = AirQualityViz()
    running = True
    frame_count = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    viz.target_year = min(2023, int(viz.target_year) + 1)  # 设置目标年份
                elif event.key == pygame.K_LEFT:
                    viz.target_year = max(1993, int(viz.target_year) - 1)  # 设置目标年份
                elif event.key == pygame.K_SPACE:
                    # 空格键暂停/继续自动播放
                    frame_count = 0
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 检测区域点击
                margin = 50
                grid_size = 3
                cell_width = (WIDTH - 2 * margin) // grid_size
                cell_height = 200
                
                mouse_x, mouse_y = event.pos
                if 100 <= mouse_y <= 700:  # 区域可视化的垂直范围
                    row = (mouse_y - 100) // cell_height
                    col = (mouse_x - margin) // cell_width
                    index = row * grid_size + col
                    if 0 <= index < len(DISTRICTS):
                        viz.selected_district = DISTRICTS[index]
                    
        viz.update_particles()
        viz.draw(screen)
        pygame.display.flip()
        
        # 每300帧自动前进一年
        frame_count += 1
        if frame_count >= 300:
            frame_count = 0
            viz.target_year = viz.target_year + 1 if viz.target_year < 2023 else 1993  # 设置目标年份而不是直接修改年份
            
        clock.tick(60)

if __name__ == "__main__":
    main()
    pygame.quit()
