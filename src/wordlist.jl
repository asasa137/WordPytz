fn = joinpath(@__DIR__, "../out/wordlist.txt")
wordgamelist = split.(readlines(fn)[1:end-1], "|")
wordgamelist = wordgamelist[allunique.(wordgamelist)]
grid = sort.(unique.(collect.(join.(wordgamelist))))
function wordlistget(wordlist)
    sort!(wordlist; lt = (x, y) -> length(x) < length(y))
    wordlist_unq = unique(wordlist)
end
wordlist = vcat(wordgamelist...)
wordlist_unq = wordlistget(wordlist)
wordgamedf = DataFrame(grid = grid, wordlist = wordgamelist)
worddf = DataFrame(word = wordlist_unq,
                    cnt = [sum(elm .== wordlist) for elm in wordlist_unq],
                    pc = size(wordgamelist, 1)
                    )
#   del1 = sort(worddf[length.(worddf.word) .== 4, :], :cnt)
function wordlist4letter(letter)
    idx1 = [letter in grid for grid in wordgamedf.grid]
    wordlist = vcat(wordgamedf.wordlist[idx1]...)
    wordlist_unq = wordlistget(wordlist)
    idx2 = occursin.(letter, wordlist_unq)
    wordlist4letterdf = DataFrame(word = wordlist_unq[idx2],
                                    cnt = [sum(elm .== wordlist) for elm in wordlist_unq[idx2]] / sum(idx1),
                                    maxi = sum(idx1)
                                )
    sort(wordlist4letterdf, :cnt)
end
display(wordlist4letter('Z'))
function wordrgx(rgx)
    wordrgxdf =  sort(worddf[.!isnothing.(match.(rgx, worddf.word)), :], :cnt)
    wordrgxdf.occ .= sum([all(@. ($collect(match(r"[A-Z]+", rgx.pattern).match) in (grid, ))) for grid in wordgamedf.grid])
    wordrgxdf
end
rgx = r"[\n]*ONT$"
display(wordrgx(rgx))
wordend = [word[(length(word)>3 ? end-2 : 1):end] for word in worddf.word]
display(plot(histogram(x = sort(wordend; lt = (xx, yy) -> sum(xx .== wordend) < sum(yy .== wordend)))))
wordstart = [word[1:(length(word)<3 ? end : 3)] for word in worddf.word]
display(plot(histogram(x = sort(wordstart; lt = (xx, yy) -> sum(xx .== wordstart) < sum(yy .== wordstart)))))
sort(worddf[.!isnothing.(match.(r"^SERI", worddf.word)), :], :cnt)
wordgamedf, worddf
