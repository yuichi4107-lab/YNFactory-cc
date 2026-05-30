import AppKit
import Foundation

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    .appendingPathComponent(".company/outputs/ebooks-manga/chatgpt55-now-only-manga")
let assets = root.appendingPathComponent("共通テンプレ")
let outDir = root.appendingPathComponent("KDP出版用")
try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)

let width = 1024
let height = 1536
let size = NSSize(width: width, height: height)

func color(_ hex: UInt32, _ alpha: CGFloat = 1.0) -> NSColor {
    NSColor(
        calibratedRed: CGFloat((hex >> 16) & 0xff) / 255.0,
        green: CGFloat((hex >> 8) & 0xff) / 255.0,
        blue: CGFloat(hex & 0xff) / 255.0,
        alpha: alpha
    )
}

func font(_ name: String, _ size: CGFloat, _ weight: NSFont.Weight) -> NSFont {
    NSFont(name: name, size: size) ?? NSFont.systemFont(ofSize: size, weight: weight)
}

func para(_ align: NSTextAlignment, _ line: CGFloat = 1.0) -> NSMutableParagraphStyle {
    let p = NSMutableParagraphStyle()
    p.alignment = align
    p.lineHeightMultiple = line
    p.lineBreakMode = .byWordWrapping
    return p
}

func drawText(_ text: String, _ rect: NSRect, _ f: NSFont, _ c: NSColor, _ align: NSTextAlignment = .left, _ line: CGFloat = 1.0, stroke: NSColor? = nil, strokeWidth: CGFloat = 0) {
    var attrs: [NSAttributedString.Key: Any] = [
        .font: f,
        .foregroundColor: c,
        .paragraphStyle: para(align, line),
        .kern: 0
    ]
    if let stroke {
        attrs[.strokeColor] = stroke
        attrs[.strokeWidth] = strokeWidth
    }
    NSString(string: text).draw(in: rect, withAttributes: attrs)
}

func rounded(_ rect: NSRect, _ radius: CGFloat, _ fill: NSColor, _ stroke: NSColor? = nil, _ line: CGFloat = 2) {
    let path = NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
    fill.setFill()
    path.fill()
    if let stroke {
        stroke.setStroke()
        path.lineWidth = line
        path.stroke()
    }
}

func polygon(_ pts: [NSPoint], fill: NSColor) {
    let path = NSBezierPath()
    path.move(to: pts[0])
    for p in pts.dropFirst() { path.line(to: p) }
    path.close()
    fill.setFill()
    path.fill()
}

func loadImage(_ name: String) -> NSImage {
    guard let img = NSImage(contentsOf: assets.appendingPathComponent(name)) else {
        fatalError("Missing image \(name)")
    }
    return img
}

func drawImage(_ image: NSImage, _ rect: NSRect, _ alpha: CGFloat = 1.0) {
    image.draw(in: rect, from: .zero, operation: .sourceOver, fraction: alpha, respectFlipped: true, hints: [.interpolation: NSImageInterpolation.high])
}

func drawCardImage(_ image: NSImage, _ rect: NSRect, border: NSColor, shadow: Bool = true) {
    if shadow {
        NSGraphicsContext.saveGraphicsState()
        let s = NSShadow()
        s.shadowColor = color(0x111827, 0.30)
        s.shadowBlurRadius = 22
        s.shadowOffset = NSSize(width: 0, height: -12)
        s.set()
        rounded(rect.insetBy(dx: -8, dy: -8), 22, color(0xffffff, 0.98), border, 4)
        NSGraphicsContext.restoreGraphicsState()
    } else {
        rounded(rect.insetBy(dx: -8, dy: -8), 22, color(0xffffff, 0.98), border, 4)
    }
    drawImage(image, rect)
}

func burst(_ center: NSPoint, _ outer: CGFloat, _ inner: CGFloat, _ count: Int, _ fill: NSColor) {
    var pts: [NSPoint] = []
    for i in 0..<(count * 2) {
        let r = i % 2 == 0 ? outer : inner
        let a = CGFloat(i) * .pi / CGFloat(count) - .pi / 2
        pts.append(NSPoint(x: center.x + cos(a) * r, y: center.y + sin(a) * r))
    }
    polygon(pts, fill: fill)
}

let img = NSImage(size: size)
img.lockFocusFlipped(true)

// Bestseller-style, high-contrast background.
NSColor.white.setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()
polygon([
    NSPoint(x: 0, y: 0), NSPoint(x: 1024, y: 0),
    NSPoint(x: 1024, y: 1010), NSPoint(x: 0, y: 860)
], fill: color(0xffd21f))
polygon([
    NSPoint(x: 0, y: 0), NSPoint(x: 340, y: 0),
    NSPoint(x: 170, y: 520), NSPoint(x: 0, y: 610)
], fill: color(0xff8a00, 0.52))
polygon([
    NSPoint(x: 1024, y: 255), NSPoint(x: 1024, y: 1030),
    NSPoint(x: 740, y: 965), NSPoint(x: 820, y: 335)
], fill: color(0x00a884, 0.35))

// Top label.
rounded(NSRect(x: 52, y: 54, width: 250, height: 62), 31, color(0x111827), color(0xffffff, 0.9), 3)
drawText("マンガでわかる", NSRect(x: 72, y: 70, width: 210, height: 34), font("Hiragino Sans", 27, .heavy), .white, .center)

rounded(NSRect(x: 722, y: 54, width: 250, height: 62), 31, color(0xef4444), color(0xffffff, 0.9), 3)
drawText("2026年5月版", NSRect(x: 744, y: 71, width: 206, height: 32), font("Hiragino Sans", 25, .heavy), .white, .center)

// Thumbnail-dominant main hook.
drawText("結論", NSRect(x: 58, y: 132, width: 230, height: 104), font("Hiragino Sans", 76, .heavy), color(0xef4444), .left, 0.95, stroke: .white, strokeWidth: -5)
drawText("ChatGPT", NSRect(x: 244, y: 176, width: 548, height: 92), font("__system__", 78, .heavy), color(0x0b1220), .center, 0.9)
drawText("だけでいい", NSRect(x: 190, y: 270, width: 650, height: 98), font("__system__", 76, .heavy), color(0xef4444), .center, 0.9)
drawText("いまは", NSRect(x: 690, y: 292, width: 190, height: 54), font("__system__", 38, .heavy), color(0x0b1220), .center, 0.9)

rounded(NSRect(x: 74, y: 476, width: 876, height: 96), 18, color(0x0f172a), color(0xffffff), 4)
drawText("ClaudeもGeminiも比較したうえで、いま何を選ぶか", NSRect(x: 98, y: 505, width: 828, height: 40), font("Hiragino Sans", 29, .heavy), .white, .center)

// Title and subtitle.
rounded(NSRect(x: 80, y: 602, width: 864, height: 132), 18, color(0xffffff, 0.92), color(0x111827), 5)
drawText("ChatGPT 5.5時代の結論", NSRect(x: 104, y: 626, width: 816, height: 56), font("Hiragino Sans", 42, .heavy), color(0x111827), .center)
drawText("一周回って、いまはChatGPTだけでいい", NSRect(x: 116, y: 684, width: 792, height: 34), font("Hiragino Sans", 25, .bold), color(0x0f766e), .center)

// Conversion promise.
burst(NSPoint(x: 154, y: 822), 116, 88, 18, color(0xef4444))
drawText("AI選びに\n迷う人へ", NSRect(x: 72, y: 775, width: 164, height: 88), font("Hiragino Sans", 28, .heavy), .white, .center, 0.95)

rounded(NSRect(x: 264, y: 770, width: 674, height: 108), 18, color(0xffffff, 0.93), color(0xef4444), 5)
drawText("比較に時間を使わず、今日の仕事を前へ進める", NSRect(x: 292, y: 804, width: 618, height: 36), font("Hiragino Sans", 30, .heavy), color(0x111827), .center)

// Character stage.
let mina = loadImage("高橋ミナ.png")
let ren = loadImage("佐伯レン.png")
let yui = loadImage("真田ユイ.png")
drawCardImage(mina, NSRect(x: 40, y: 902, width: 310, height: 465), border: color(0x2563eb))
drawCardImage(ren, NSRect(x: 336, y: 850, width: 360, height: 540), border: color(0x111827))
drawCardImage(yui, NSRect(x: 688, y: 910, width: 304, height: 456), border: color(0x16a34a))

rounded(NSRect(x: 96, y: 1358, width: 832, height: 58), 29, color(0xffffff), color(0x111827), 4)
drawText("実務ワークフロー・プロンプト例・乗り換え判断まで", NSRect(x: 124, y: 1375, width: 776, height: 30), font("Hiragino Sans", 24, .heavy), color(0x111827), .center)

// Bottom author band.
polygon([
    NSPoint(x: 0, y: 1440), NSPoint(x: 1024, y: 1392),
    NSPoint(x: 1024, y: 1536), NSPoint(x: 0, y: 1536)
], fill: color(0x111827))
drawText("Yuichi", NSRect(x: 0, y: 1466, width: 1024, height: 42), font("Helvetica Neue", 31, .bold), .white, .center)

img.unlockFocus()

guard let tiff = img.tiffRepresentation, let bitmap = NSBitmapImageRep(data: tiff) else {
    fatalError("Failed to create bitmap")
}

let pngURL = outDir.appendingPathComponent("cover.png")
let jpgURL = outDir.appendingPathComponent("cover.jpg")
try bitmap.representation(using: .png, properties: [:])!.write(to: pngURL)
try bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.92])!.write(to: jpgURL)
print(pngURL.path)
print(jpgURL.path)
