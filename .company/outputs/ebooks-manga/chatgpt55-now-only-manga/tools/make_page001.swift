import AppKit
import Foundation

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    .appendingPathComponent(".company/outputs/ebooks-manga/chatgpt55-now-only-manga")
let outDir = root.appendingPathComponent("panels/pages")
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

func font(_ size: CGFloat, _ weight: NSFont.Weight) -> NSFont {
    NSFont(name: "Hiragino Sans", size: size) ?? NSFont.systemFont(ofSize: size, weight: weight)
}

func para(_ align: NSTextAlignment, _ line: CGFloat = 1.0) -> NSMutableParagraphStyle {
    let p = NSMutableParagraphStyle()
    p.alignment = align
    p.lineHeightMultiple = line
    p.lineBreakMode = .byWordWrapping
    return p
}

func drawText(_ text: String, _ rect: NSRect, _ f: NSFont, _ c: NSColor, _ align: NSTextAlignment = .center, _ line: CGFloat = 1.0) {
    let attrs: [NSAttributedString.Key: Any] = [
        .font: f,
        .foregroundColor: c,
        .paragraphStyle: para(align, line),
        .kern: 0
    ]
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

let img = NSImage(size: size)
img.lockFocusFlipped(true)

color(0xffffff).setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()
polygon([
    NSPoint(x: 0, y: 0), NSPoint(x: 1024, y: 0),
    NSPoint(x: 1024, y: 410), NSPoint(x: 0, y: 300)
], fill: color(0x0f2a44))
polygon([
    NSPoint(x: 0, y: 270), NSPoint(x: 1024, y: 405),
    NSPoint(x: 1024, y: 510), NSPoint(x: 0, y: 380)
], fill: color(0x15b8d6))
polygon([
    NSPoint(x: 0, y: 1080), NSPoint(x: 1024, y: 960),
    NSPoint(x: 1024, y: 1536), NSPoint(x: 0, y: 1536)
], fill: color(0xffd43b))

rounded(NSRect(x: 96, y: 140, width: 832, height: 78), 12, color(0xffd43b))
drawText("マンガでわかる", NSRect(x: 96, y: 156, width: 832, height: 58), font(42, .bold), color(0x0f172a))

drawText("ChatGPT 5.5\n時代の結論", NSRect(x: 92, y: 450, width: 840, height: 270), font(88, .heavy), color(0x0f172a), .center, 0.92)
drawText("一周回って、いまは\nChatGPTだけでいい", NSRect(x: 116, y: 760, width: 792, height: 165), font(46, .bold), color(0x0f172a), .center, 1.05)

rounded(NSRect(x: 132, y: 1022, width: 760, height: 250), 20, color(0xffffff), color(0x0f2a44), 4)
drawText("はじめに / 第1章 / 第2章 / 第3章\n第4章 / 第5章 / おわりに", NSRect(x: 172, y: 1072, width: 680, height: 130), font(34, .medium), color(0x0f172a), .center, 1.25)
drawText("AIツール選びに迷う時間を終わらせ、\n今日の仕事を前に進めるための実用マンガ。", NSRect(x: 132, y: 1265, width: 760, height: 110), font(30, .medium), color(0x334155), .center, 1.2)

drawText("Yuichi", NSRect(x: 0, y: 1448, width: 1024, height: 54), font(30, .bold), color(0x0f172a))

img.unlockFocus()

guard
    let tiff = img.tiffRepresentation,
    let bitmap = NSBitmapImageRep(data: tiff),
    let jpg = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.92])
else {
    fatalError("failed to render P001")
}

try jpg.write(to: outDir.appendingPathComponent("P001.jpg"))
print(outDir.appendingPathComponent("P001.jpg").path)
