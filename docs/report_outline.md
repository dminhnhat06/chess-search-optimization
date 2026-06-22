# Dàn ý báo cáo thí nghiệm

## 1. Giới thiệu

- Bối cảnh: tìm kiếm là thành phần trung tâm trong AI chơi cờ vua.
- Vấn đề: minimax cơ bản dễ bùng nổ số node khi tăng độ sâu.
- Mục tiêu: đánh giá hiệu quả của các kỹ thuật tối ưu tìm kiếm qua các preset
  V0-V5.
- Phạm vi: tập trung vào benchmark vị trí FEN, không khẳng định sức mạnh chơi
  cờ tuyệt đối.

## 2. Cơ sở lý thuyết

- Biểu diễn trạng thái bàn cờ và nước đi hợp lệ.
- Hàm đánh giá thế cờ.
- Minimax.
- Alpha-beta pruning.
- Move ordering.
- Transposition table.
- Iterative deepening.
- Quiescence search và horizon effect.
- Các chỉ số đo hiệu năng: node, thời gian, NPS, cutoff, TT hit rate.

## 3. Thiết kế hệ thống

- Kiến trúc module:
  - `engine`: điều phối search, config, limits, result, metrics.
  - `search`: hiện thực V0, V1, V4, V5 và logic alpha-beta.
  - `optimization`: move ordering, transposition table, search controller.
  - `presets`: factory tạo engine V0-V5.
  - `experiments`: loader FEN và benchmark runner.
  - `scripts`: chạy benchmark và phân tích kết quả.
- Luồng chạy một lượt benchmark:
  - Load FEN.
  - Tạo engine theo preset.
  - Reset engine trước mỗi vị trí.
  - Search với `SearchLimits`.
  - Ghi một dòng kết quả.
- Cách đảm bảo tái lập:
  - Cùng dataset.
  - Cùng depth hoặc movetime.
  - Cùng repeat count.
  - Cùng môi trường chạy khi so sánh thời gian.

## 4. Thiết kế thí nghiệm

- Dataset:
  - `opening`
  - `middlegame`
  - `tactical`
  - `check`
  - `endgame`
  - `quiescence`
- Preset:
  - V0: minimax.
  - V1: alpha-beta.
  - V2: alpha-beta + move ordering.
  - V3: alpha-beta + move ordering + transposition table.
  - V4: iterative deepening.
  - V5: quiescence search.
- Chế độ thí nghiệm:
  - Fixed depth: so sánh số node và pruning tại cùng độ sâu.
  - Fixed time: so sánh độ sâu đạt được trong cùng thời gian.
- Cấu hình khuyến nghị:
  - Smoke test nhỏ để kiểm tra pipeline.
  - Benchmark chính depth 1-3 cho toàn bộ V0-V5.
  - Benchmark depth 4 bổ sung cho V1-V5 nếu V0 quá chậm.
- Metric:
  - `total_nodes`
  - `elapsed_ms`
  - `nps`
  - `cutoffs`
  - `cutoff_rate`
  - `tt_hit_rate`
  - `qnodes_searched`
  - `accuracy`
  - `depth_reached`
  - `seldepth`

## 5. Kết quả thực nghiệm

- Trình bày bảng tổng hợp theo preset và depth.
- Trình bày bảng tổng hợp theo category.
- Trình bày node reduction so với baseline.
- Trình bày speedup so với baseline.
- Trình bày TT hit rate cho các preset có transposition table.
- Trình bày qnodes và seldepth khi so sánh V3 với V5.
- Trình bày accuracy chỉ trên các vị trí có `best_move`.
- Chèn các biểu đồ được tạo từ `scripts/analyze_results.py`.
- Không đưa số liệu smoke test vào phần kết quả chính.

## 6. Nhận xét

- V0-V1: mức giảm node do alpha-beta.
- V1-V2: ảnh hưởng của move ordering tới cutoff.
- V2-V3: mức độ hữu ích của transposition table.
- V3-V4: lợi ích và chi phí của iterative deepening.
- V3-V5: tác động của quiescence search tới tactical positions.
- Khác biệt giữa các category:
  - Opening thường có branching factor lớn.
  - Tactical và quiescence nhạy với horizon effect.
  - Endgame phù hợp để quan sát độ sâu.
- Phân biệt rõ hiệu quả tìm kiếm và sức mạnh chơi cờ.

## 7. Kết luận

- Tóm tắt kỹ thuật nào giảm node rõ nhất.
- Tóm tắt kỹ thuật nào cải thiện độ ổn định chiến thuật.
- Tóm tắt trade-off giữa tốc độ, số node, độ sâu và độ chính xác.
- Nêu lại giới hạn của dataset và môi trường chạy.

## 8. Hướng phát triển

- Cải thiện hàm đánh giá.
- Mở rộng dataset benchmark.
- Thêm opening book hoặc EPD test suites chuẩn.
- Thêm time management thực tế cho UCI.
- Chạy fastchess tournament để bổ sung bằng chứng về playing strength.
- Thêm thống kê độ tin cậy cho benchmark nhiều repeat.
- Tối ưu transposition table và move ordering nâng cao.
