# 🚌 Đánh Giá Tổng Thể Mạng Lưới Xe Buýt (v3)

> Công cụ đánh giá hiệu suất mạng lưới xe buýt dựa trên kết quả mô phỏng **MATSim**. Hỗ trợ so sánh nhiều kịch bản (scenario) và xuất ra các chỉ số KPI + biểu đồ trực quan.

---

## 📖 Mục Lục

- [Tổng Quan](#-tổng-quan)
- [Kiến Trúc Dự Án](#-kiến-trúc-dự-án)
- [Yêu Cầu Hệ Thống](#-yêu-cầu-hệ-thống)
- [Cài Đặt](#-cài-đặt)
- [Chuẩn Bị Dữ Liệu Đầu Vào](#-chuẩn-bị-dữ-liệu-đầu-vào)
- [Cấu Hình](#-cấu-hình)
- [Cách Chạy](#-cách-chạy)
- [Kết Quả Đầu Ra](#-kết-quả-đầu-ra)
- [Các Chỉ Số KPI](#-các-chỉ-số-kpi)
- [Cấu Trúc Module Chi Tiết](#-cấu-trúc-module-chi-tiết)
- [Quy Trình Xử Lý (Pipeline)](#-quy-trình-xử-lý-pipeline)

---

## 🎯 Tổng Quan

Dự án này nhận đầu vào là kết quả mô phỏng giao thông từ **MATSim** (network, plan, events, transit schedule, transit vehicle) và thực hiện:

1. **Trích xuất dữ liệu sự kiện** (events) thành các bảng trung gian (Arrow format)
2. **Tính toán các chỉ số KPI** đánh giá hiệu suất mạng lưới xe buýt
3. **Tạo biểu đồ trực quan** (heatmap tuyến xe buýt, heatmap OD, phân tích chuyến đi)
4. **So sánh nhiều kịch bản** (ví dụ: *baseline* vs *after*) và ghép ảnh so sánh

---

## 🏗 Kiến Trúc Dự Án

```
📦 v3_Danh_Gia_Tong_The_MangLuoiXeBus/
├── 📄 README.md                  # File này
├── 📄 requirements.txt           # Danh sách thư viện Python
│
├── 📁 config/                    # Cấu hình YAML
│   ├── config_path.yaml          # Đường dẫn input/output cho từng scenario
│   └── config_param.yaml         # Tham số tính toán (zone, OTP, visualize...)
│
├── 📁 scenario/                  # Dữ liệu đầu vào MATSim (mỗi scenario 1 thư mục)
│   ├── baseline/                 # Kịch bản gốc
│   │   ├── network.xml
│   │   ├── plan.xml
│   │   ├── output_events.xml
│   │   ├── output_trips.csv
│   │   ├── output_legs.csv
│   │   ├── output_plans.xml
│   │   ├── output_transitVehicles.xml
│   │   └── output_transitSchedule.xml
│   └── after/                    # Kịch bản sau điều chỉnh
│       └── ... (cùng cấu trúc)
│
├── 📁 src/                       # Mã nguồn chính
│   ├── Main_v2.py                # ⭐ Entry point chính (chạy multi-scenario)
│   ├── Main_v1.py                # Entry point cũ (chạy single scenario)
│   │
│   ├── 📁 data/                  # Load config
│   │   └── load_config.py
│   ├── 📁 domain/                # Các class cơ bản
│   │   ├── point.py              # Class Point (x, y)
│   │   └── logic.py              # Logic helpers
│   ├── 📁 network/               # Xử lý mạng lưới giao thông
│   │   ├── network.py            # Parse network.xml → nodes & links dict
│   │   └── core_class.py         # Tính boundary của network
│   ├── 📁 plan/                  # Xử lý kế hoạch di chuyển
│   │   ├── plan.py               # Parse plan.xml → people activities dict
│   │   └── core_class.py         # Tính boundary của plans
│   ├── 📁 transit/               # Xử lý transit (xe buýt, lịch trình)
│   │   ├── transit_schedule.py   # Parse transitSchedule.xml → routes & stops
│   │   ├── transit_vehicle.py    # Parse transitVehicles.xml → vehicle type dict
│   │   └── core_class.py
│   ├── 📁 od_mask/               # Tạo lưới vùng OD (Origin-Destination)
│   │   ├── generator.py          # ZoneGeneratorByGrid - tạo zone grid
│   │   └── core_class.py         # Class Zone
│   ├── 📁 events/                # Trích xuất sự kiện từ output_events.xml
│   │   ├── person_trip.py        # Chuyến đi cá nhân (OD, thời gian, zone)
│   │   ├── person_enter_bus.py   # Sự kiện hành khách lên xe buýt
│   │   ├── travel_time.py        # Thời gian di chuyển các phương tiện
│   │   ├── bus_delay.py          # Độ trễ xe buýt tại trạm
│   │   └── bus_trip.py           # Chuyến đi của xe buýt (km, thời gian)
│   ├── 📁 performance_measurement/  # Tính toán KPI
│   │   ├── ridership.py          # Số người sử dụng xe buýt
│   │   ├── service_coverage.py   # Độ bao phủ dịch vụ
│   │   ├── otp.py                # On-Time Performance (đúng giờ)
│   │   ├── travel_time_ratio.py  # Tỉ lệ thời gian Bus/Car
│   │   ├── bus_route_info.py     # Thông số trung bình tuyến (km, trạm)
│   │   ├── bus_productivity_effeciency.py  # Năng suất & hiệu quả
│   │   └── bus_transfer_rate.py  # Tỉ lệ chuyển tuyến
│   ├── 📁 visualize/             # Tạo biểu đồ
│   │   ├── busroute_heatmap.py   # Heatmap tuyến xe buýt trên mạng lưới
│   │   ├── od_heatmap.py         # Heatmap OD (Origin-Destination)
│   │   ├── person_trip_analysis.py  # Phân tích chuyến đi (Top OD, thống kê)
│   │   ├── compare.py            # So sánh giữa các scenario
│   │   └── merge_image.py        # Ghép ảnh so sánh
│   └── 📁 utils/                 # Tiện ích
│       └── folder_creator.py     # Tự động tạo thư mục output
│
└── 📁 data/                      # Dữ liệu đầu ra (tự động tạo)
    ├── interim/{scenario}/event/  # Dữ liệu trung gian (.arrow)
    ├── visualize/{scenario}/      # Ảnh biểu đồ (.png)
    ├── processed/{scenario}/      # Kết quả KPI (.txt)
    └── visualize/comparison/      # Ảnh so sánh giữa các scenario
```

---

## 💻 Yêu Cầu Hệ Thống

- **Python** 3.10+
- **RAM** ≥ 8 GB (khuyến nghị, do xử lý file XML lớn)
- **Hệ điều hành**: Windows / Linux / macOS

---

## ⚙ Cài Đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd v3_Danh_Gia_Tong_The_MangLuoiXeBus
```

### 2. Tạo virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

### 3. Cài đặt thư viện

```bash
pip install -r requirements.txt
```

**Các thư viện chính:**

| Thư viện | Mục đích |
|---|---|
| `pandas` | Xử lý dữ liệu bảng |
| `pyarrow` | Đọc/ghi file Arrow (dữ liệu trung gian) |
| `lxml` | Parse file XML (network, events, plan...) |
| `matplotlib` | Vẽ biểu đồ |
| `shapely` | Xử lý hình học (zone, coverage) |
| `scipy` | Tính toán khoa học |
| `omegaconf` | Quản lý config YAML |
| `numpy` | Tính toán số |

---

## 📂 Chuẩn Bị Dữ Liệu Đầu Vào

Mỗi scenario cần đặt trong thư mục `scenario/<tên_scenario>/` với các file sau từ kết quả chạy MATSim:

| File | Mô tả |
|---|---|
| `network.xml` | Mạng lưới giao thông (nodes & links) |
| `plan.xml` | Kế hoạch di chuyển của dân cư |
| `output_events.xml` | Toàn bộ sự kiện mô phỏng |
| `output_trips.csv` | Thông tin các chuyến đi |
| `output_legs.csv` | Chi tiết từng chặng đi |
| `output_plans.xml` | Kế hoạch di chuyển đầu ra |
| `output_transitVehicles.xml` | Thông tin phương tiện công cộng |
| `output_transitSchedule.xml` | Lịch trình tuyến xe buýt |

> ⚠️ **Lưu ý:** Tên thư mục scenario phải khớp với giá trị trong `config_path.yaml` → `scenario_list`.

---

## 🔧 Cấu Hình

### `config/config_path.yaml` – Đường dẫn dữ liệu

```yaml
scenario: "after"                    # Scenario mặc định
scenario_list: ["baseline", "after"] # Danh sách scenario cần chạy

paths:                               # Đường dẫn input (dùng ${scenario} để interpolate)
  network: "scenario/${scenario}/network.xml"
  plan: "scenario/${scenario}/plan.xml"
  events: "scenario/${scenario}/output_events.xml"
  # ... (xem file gốc để biết đầy đủ)

data:                                # Đường dẫn output
  interim:                           # Dữ liệu trung gian
    event:
      person_enter_bus: "data/interim/${scenario}/event/person_enter_bus.arrow"
      # ...
  processed:                         # Kết quả cuối
    kpi_result: "data/processed/${scenario}/kpi_result.txt"
    all_kpi_result: "data/processed/all_kpi_result.txt"
```

**Cách thêm scenario mới:** Thêm tên vào `scenario_list` và tạo thư mục tương ứng trong `scenario/`.

### `config/config_param.yaml` – Tham số tính toán

```yaml
bus_route_hint_str: "bus"          # Chuỗi nhận diện tuyến xe buýt

zone:
  cols: 20                         # Số cột lưới OD
  rows: 20                         # Số hàng lưới OD
  radia_m: 400.0                   # Bán kính phục vụ trạm (mét)

service_coveraged:
  act_coveraged: "home"            # Loại hoạt động tính coverage

otp:
  max_delay: 180                   # Ngưỡng trễ tối đa (giây) → vẫn tính đúng giờ
  min_delay: -180                  # Ngưỡng sớm tối đa (giây)

travel_time:
  before_bus_avg_time: 3247.26     # Thời gian bus trung bình TRƯỚC cải tiến (giây)

productivity:
  coefficient: 36                  # Hệ số chuẩn năng suất

visualize:
  od_heatmap:
    od_visualize_number: 25        # Số cặp OD hiển thị trên heatmap
  bus_heatmap:
    max_busroute_number_to_draw: 6 # Giới hạn tuyến vẽ trên heatmap
  person_trip_analysis:
    od_visualize_number: 5         # Số Top OD phân tích chi tiết
```

---

## 🚀 Cách Chạy

### Chạy đánh giá đầy đủ (multi-scenario, khuyến nghị)

```bash
python -m src.Main_v2
```

Lệnh này sẽ:
1. Chạy **từng scenario** trong `scenario_list` (ví dụ: `baseline` → `after`)
2. Tính KPI cho mỗi scenario
3. So sánh các scenario với nhau
4. Ghép ảnh so sánh side-by-side

### Chạy đánh giá đơn scenario (phiên bản cũ)

```bash
python -m src.Main_v1
```

> Chỉ chạy scenario được chỉ định trong `config_path.yaml` → `scenario`.

---

## 📊 Kết Quả Đầu Ra

Sau khi chạy, kết quả được lưu trong thư mục `data/`:

### 1. Dữ liệu trung gian (`data/interim/{scenario}/event/`)

| File | Nội dung |
|---|---|
| `person_enter_bus.arrow` | Danh sách sự kiện hành khách lên xe buýt |
| `travel_time_all_vehicle.arrow` | Thời gian di chuyển tất cả phương tiện |
| `bus_delay_at_facilities.arrow` | Độ trễ xe buýt tại từng trạm |
| `people_trip.arrow` | Chuyến đi cá nhân (OD zone, thời gian, mode) |
| `bus_trip.arrow` | Chuyến đi xe buýt (quãng đường, thời gian) |

### 2. Biểu đồ (`data/visualize/{scenario}/`)

| File | Nội dung |
|---|---|
| `bus_od_heatmap.png` | Heatmap tần suất tuyến xe buýt trên mạng lưới |
| `od_heatmap.png` | Heatmap OD hành khách |
| `person_trip_analysis/` | Thư mục chứa các biểu đồ phân tích chuyến đi |

### 3. Kết quả KPI (`data/processed/`)

| File | Nội dung |
|---|---|
| `{scenario}/kpi_result.txt` | KPI chi tiết cho từng scenario |
| `all_kpi_result.txt` | Tổng hợp KPI tất cả scenario |

### 4. So sánh (`data/visualize/comparison/`)

| File | Nội dung |
|---|---|
| `Merged_Bus_OD_Heatmap.png` | So sánh heatmap tuyến buýt giữa 2 scenario |
| `Merged_Global_Summary.png` | So sánh tổng quan giữa 2 scenario |

---

## 📈 Các Chỉ Số KPI

| # | KPI | Mô tả | Đơn vị |
|---|---|---|---|
| 1 | **Ridership** | Số người duy nhất sử dụng xe buýt / tổng dân | % |
| 2 | **Service Coverage** | Tỉ lệ dân cư sống trong bán kính phục vụ trạm | % |
| 3 | **OTP (On-Time Performance)** | Tỉ lệ chuyến xe buýt đến đúng giờ (±180s) | % |
| 4 | **Bus Travel Time Ratio (After/Before)** | So sánh thời gian bus trước và sau cải tiến | Tỉ lệ |
| 5 | **Bus/Car Travel Time Ratio** | Thời gian đi bus trung bình / thời gian đi ô tô | Tỉ lệ |
| 6 | **Productivity Index** | Hiệu suất phục vụ (ridership / giờ vận hành) | Chỉ số |
| 7 | **Efficiency Index** | Hiệu quả vận hành (ridership / tổng km) | Chỉ số |
| 8 | **Effective Distance Ratio** | Tỉ lệ km vận hành hiệu quả / tổng km | Tỉ lệ |
| 9 | **Trạm dừng TB/tuyến** | Số trạm dừng trung bình mỗi tuyến | Trạm |
| 10 | **Chiều dài TB/tuyến** | Chiều dài trung bình mỗi tuyến | km |

---

## 🧩 Cấu Trúc Module Chi Tiết

### `src/data/` – Quản lý cấu hình
- `load_config.py`: Đọc file YAML bằng **OmegaConf**, hỗ trợ biến interpolation `${scenario}`.

### `src/domain/` – Đối tượng cơ bản
- `point.py`: Class `Point(x, y)` – tọa độ 2D.
- `logic.py`: Các hàm logic hỗ trợ.

### `src/network/` – Xử lý mạng lưới
- `network.py`: Parse `network.xml` → `nodes_dict` (id → Point) và `links_dict` (id → thông tin link).
- `core_class.py`: Tìm boundary (min/max) của mạng lưới.

### `src/plan/` – Xử lý kế hoạch di chuyển
- `plan.py`: Parse `plan.xml` → `people_dict` (person_id → danh sách activities với tọa độ).
- `core_class.py`: Tìm boundary của plans.

### `src/transit/` – Xử lý giao thông công cộng
- `transit_schedule.py`: Parse `transitSchedule.xml` → `bus_routes_dict` và `bus_stops_dict`.
- `transit_vehicle.py`: Parse `transitVehicles.xml` → `vehicle_type_dict` (vehicle_id → loại phương tiện).

### `src/od_mask/` – Lưới vùng OD
- `generator.py`: `ZoneGeneratorByGrid` – chia mạng lưới thành grid (rows × cols), mỗi ô là một zone, gán mỗi chuyến đi vào zone tương ứng.
- `core_class.py`: Class `Zone` chứa thông tin từng ô.

### `src/events/` – Trích xuất sự kiện
Đọc file `output_events.xml` (thường rất lớn) và trích xuất thành các bảng Arrow:
- `person_trip.py`: Chuyến đi hành khách (origin, destination, zone, thời gian).
- `person_enter_bus.py`: Sự kiện lên xe buýt (person_id, vehicle_id, thời gian).
- `travel_time.py`: Thời gian di chuyển cho từng phương tiện.
- `bus_delay.py`: Độ trễ xe buýt tại mỗi trạm (so với lịch trình).
- `bus_trip.py`: Thông tin hành trình xe buýt (km thực tế, km hiệu quả).

### `src/performance_measurement/` – Tính toán KPI
- `ridership.py`: Đếm unique persons sử dụng xe buýt.
- `service_coverage.py`: Tỉ lệ dân trong vùng phủ sóng (bán kính quanh trạm).
- `otp.py`: Tỉ lệ chuyến đúng giờ (delay trong ngưỡng cho phép).
- `travel_time_ratio.py`: Tính thời gian trung bình bus/car và các tỉ lệ so sánh.
- `bus_route_info.py`: Thống kê trung bình tuyến (km, số trạm).
- `bus_productivity_effeciency.py`: Chỉ số năng suất, hiệu quả, tỉ lệ quãng đường hiệu quả.
- `bus_transfer_rate.py`: Tỉ lệ chuyển tuyến.

### `src/visualize/` – Trực quan hóa
- `busroute_heatmap.py`: Vẽ các tuyến xe buýt lên mạng lưới, tô màu theo tần suất.
- `od_heatmap.py`: Vẽ heatmap OD zone (top cặp OD có lượng trip lớn nhất).
- `person_trip_analysis.py`: Phân tích chi tiết chuyến đi (Top OD, phân bố, thống kê).
- `compare.py`: So sánh biểu đồ giữa nhiều scenario.
- `merge_image.py`: Ghép 2 ảnh cạnh nhau (side-by-side).

---

## 🔄 Quy Trình Xử Lý (Pipeline)

Khi chạy `Main_v2.py`, chương trình thực hiện các bước sau **cho mỗi scenario**:

```
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 1: ĐỌC DỮ LIỆU ĐẦU VÀO                                    │
│  ├── network.xml        → nodes_dict, links_dict                   │
│  ├── plan.xml           → people_dict (activities + tọa độ)        │
│  ├── transitSchedule    → bus_route_dict, bus_stops_dict            │
│  └── transitVehicles    → vehicle_type_dict                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 2: TẠO LƯỚI VÙNG OD (ZONE GRID)                             │
│  └── Chia không gian thành grid rows × cols → zone_list            │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 3: TRÍCH XUẤT SỰ KIỆN → FILE ARROW TRUNG GIAN               │
│  ├── output_events.xml → person_enter_bus.arrow                     │
│  ├── output_events.xml → travel_time_all_vehicle.arrow              │
│  ├── output_events.xml → bus_delay_at_facilities.arrow              │
│  ├── output_events.xml → people_trip.arrow                          │
│  └── output_events.xml → bus_trip.arrow                             │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 4: TÍNH TOÁN CÁC CHỈ SỐ KPI                                 │
│  ├── Ridership, Service Coverage, OTP                               │
│  ├── Travel Time Ratio (Bus/Car, Before/After)                      │
│  ├── Productivity Index, Efficiency Index                           │
│  └── Effective Distance Ratio, thông số tuyến                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 5: TẠO BIỂU ĐỒ TRỰC QUAN                                    │
│  ├── Heatmap tuyến xe buýt                                          │
│  ├── Heatmap OD                                                     │
│  └── Phân tích chuyến đi cá nhân (Top OD)                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 6: XUẤT KẾT QUẢ KPI → FILE TXT                               │
└─────────────────────────────────────────────────────────────────────┘
```

**Sau khi chạy tất cả scenario:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 7: SO SÁNH GIỮA CÁC SCENARIO                                │
│  ├── Plot so sánh chuyến đi giữa các scenario                      │
│  └── Ghép ảnh side-by-side (Bus Heatmap, Global Summary)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ❓ FAQ

**Q: File `output_events.xml` quá lớn, chạy lâu?**
> Đây là bước tốn thời gian nhất. Dữ liệu trung gian được lưu dưới dạng `.arrow` để tối ưu tốc độ đọc/ghi. Lần chạy đầu sẽ lâu, nhưng nếu chỉnh code phần KPI/visualize, bạn có thể comment bước 3 để dùng lại file `.arrow` đã tạo.

**Q: Muốn thêm scenario mới?**
> 1. Tạo thư mục `scenario/<tên_mới>/` và copy dữ liệu MATSim vào.
> 2. Thêm `"<tên_mới>"` vào `scenario_list` trong `config/config_path.yaml`.
> 3. Chạy lại `python -m src.Main_v2`.

**Q: Muốn thay đổi bán kính phục vụ?**
> Chỉnh `radia_m` trong `config/config_param.yaml` (đơn vị: mét).

---

## 📝 Ghi Chú

- Dữ liệu trong thư mục `data/` và `scenario/` được gitignore, không commit lên repository.
- File `Main_v1.py` là phiên bản cũ (single scenario), `Main_v2.py` là phiên bản mới (multi-scenario + so sánh).
- Thư mục `DATA da danh gia/` chứa các kết quả đánh giá trước đó (tham khảo).
