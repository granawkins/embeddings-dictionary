import React from 'react'
import { useCallback } from 'react';
import { useState, useEffect, useRef } from 'react';
import { Canvas } from '@react-three/fiber'

import Dot from './Dot';
import Camera from './Camera';
import FAQButton from './navigation/FAQ';
import LoadingHandler from './LoadingHandler';
import ErrorModal from './ErrorModal';
import Navigation from './navigation/Navigation';
import { debounce, fetchWithAuth } from './utils';

interface DotData {
    word: string;
    x: number;
    y: number;
    z: number;
    language: string | null;
}

interface Corpus {
    [key: string]: DotData;
}

interface SearchRequest {
    word: string;
    l1: string;
    l2: null;
    words_per_l: number;
}

const DotMemo = React.memo(Dot);

const App: React.FC = () => {
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [corpus, setCorpus] = useState<Corpus>({});
    const [inputText, setInputText] = useState<string>("when u don't wanna get out of bed");
    const [activeText, setActiveText] = useState<string>("");
    const [searchPending, setSearchPending] = useState<boolean>(false);
    const wordsPerL = 20;

    const timer = useRef<NodeJS.Timeout | null>(null);
    const [selected, setSelected] = useState<string[]>([]);
    
    const select = (word: string) => {
        setSelected(oldSelected => {
            if (oldSelected.includes(word)) return oldSelected.filter(w => w !== word);
            return [...oldSelected, word];
        });
    };
    
    const handleSearch = useCallback(() => {
        if (!inputText || inputText === activeText) return;
        if (timer.current) clearTimeout(timer.current);
        setSearchPending(true);
        timer.current = setTimeout(() => {
            setLoading(true);
            try {
                const searchRequest: SearchRequest = {
                    word: inputText,
                    l1: "english",
                    l2: null,
                    words_per_l: wordsPerL,
                };
                
                fetchWithAuth<Corpus>(
                    "/api/search",
                    "POST",
                    searchRequest
                )
                    .then(data => {
                        console.log(data);
                        setActiveText(inputText);
                        setCorpus(data);
                        setSearchPending(false);
                    })
                    .catch(error => {
                        setError(error.message);
                        setSearchPending(false);
                    })
                    .finally(() => {
                        setLoading(false);
                    });
            } catch (error) {
                if (error instanceof Error) {
                    setError(error.message);
                } else {
                    setError('An unknown error occurred');
                }
                setSearchPending(false);
                setLoading(false);
            }
        }, 1000);
    }, [inputText, activeText]);
    
    useEffect(() => {
        handleSearch();
    }, [handleSearch]);

    return (
        <>
            <Navigation 
                inputText={inputText}
                setInputText={setInputText}
                handleSearch={handleSearch}
                loading={loading}
            />
            <LoadingHandler isLoading={loading} />
            <Canvas>
                <ambientLight />
                <pointLight position={[10, 10, 10]} />
                <Camera selectedCorpus={corpus} />
                {corpus &&
                    Object.entries(corpus).map(([_, data]) => (
                        <DotMemo 
                            key={data.word} 
                            word={data.word} 
                            x={data.x} 
                            y={data.y} 
                            z={data.z}
                            selected={selected.includes(data.word)}
                            select={() => select(data.word)}
                            searchPending={searchPending}
                        />
                    ))}
                {/* A red dot at the origin to represent the search term */}
                <DotMemo 
                    word={inputText} 
                    x={0} 
                    y={0} 
                    z={0}
                    selected={selected.includes(inputText)}
                    select={() => select(inputText)}
                    color="red"
                    searchPending={searchPending}
                />
            </Canvas>
            <FAQButton />
            {error && <ErrorModal message={error} onClose={() => setError(null)} />}
        </>
    );
};

export default App;
