import React from 'react'
import { useState, useEffect } from 'react';
import { OrbitControls } from '@react-three/drei';
import { Canvas } from '@react-three/fiber'

import Dot from './Dot';
import SearchBox from './SearchBox';

/*
ACTIONS TO SUPPORT
1. Load page (/api)
2. Search for word ()
*/

const fetchApi = async (route="/api", method="GET", args={}) => {
    try {
        const response = await fetch(route, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(args),
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.log(error);
    }
}


const App = () => {

    const [isLoading, setIsLoading] = useState(false)
    const [pcaId, setPcaId] = useState("default");
    const [corpus, setCorpus] = useState({});
    const [searchTerm, setSearchTerm] = useState([])
    const [searchHistory, setSearchHistory] = useState([])


    // On page load -> set default corpus, oxford 3000
    const fetchIndex = async () => {
        setIsLoading(true)
        try {
            const response = await fetch("/api/index")
            const data = await response.json()
            console.log(data)
            const newCorpus = { ...corpus }
            Object.entries(data.vectors).forEach(([word, coordinates]) => {
                newCorpus[word] = { coordinates, selected: false }
            })
            setPcaId(data.pca_id)
            setCorpus(newCorpus)
        } finally {
            setIsLoading(false)
        }
    };
    useEffect(() => {
        if (Object.keys(corpus).length === 0 && !isLoading) {
            console.log('ello')
            fetchIndex()
        }
    }, []);


    // Press enter on search box -> add any new words to corpus, reset selected
    const search = async (words) => {
        setIsLoading(true)
        try {
            const newWords = words.filter(word => !Object.keys(corpus).includes(word))
            const newCorpus = { ...corpus }
            if (newWords.length > 0) {
                const data = await fetchApi("/api/search", "POST", {words: newWords, pca_id: pcaId});
                Object.entries(data.vectors).forEach(([word, coordinates]) => {
                    newCorpus[word] = { coordinates, selected: false }
                })
                setPcaId(data.pca_id);
            }
            for (let word in newCorpus) {
                if (words.includes(word)) {
                    newCorpus[word].selected = true
                } else {
                    newCorpus[word].selected = false
                }
            }
            setCorpus(newCorpus);
            setSearchHistory(oldSearchHistory => [...oldSearchHistory, ...words]);
        } catch (error) {
            console.log(error);
        } finally {
            setIsLoading(false)
        }
    }
    useEffect(() => {
        if (!searchTerm || searchTerm.length === 0) {
            return
        }
        search(searchTerm)
    }, [searchTerm])


    // Click on setPCA -> update all coordinates, old and new, based on searchTerm
    const setPca = async () => {
        setIsLoading(true)
        try {
            const args = {words: searchTerm, search_history: searchHistory}
            const data = await fetchApi("/api/pca", "POST", args);
            const expectedKeys = Set([ ...Object.keys(corpus), ...searchHistory, ...searchTerm ]);
            const newCorpus = {}
            expectedKeys.forEach(word => {
                if (!Object.keys(data.vectors).includes(word)) {
                    throw new Error("PCA returned wrong number of results");
                }
                newCorpus[word] = { coordinates: data.vectors[word], selected: false }
            })
            setPcaId(data.pca_id);
            setCorpus(newCorpus);
        } catch (error) {
            console.log(error);
        } finally {
            setIsLoading(false)
        }
    }


    // Click on a dot -> it's selected
    const select = (word) => {
        const newCorpus = { ...corpus }
        newCorpus[word].selected = !newCorpus[word].selected
        setCorpus(newCorpus)
    }


    return (
        <>
            <SearchBox setSearchTerms={setSearchTerm} isLoading={isLoading} />
            {isLoading && <div className="loading">Loading...</div>}
            <Canvas>
                <ambientLight />
                <pointLight position={[10, 10, 10]} />
                <perspectiveCamera position={[0, 0, 5]} />
                <OrbitControls />
                {corpus &&
                    Object.entries(corpus).map(([word, data], i) => (
                        <Dot key={word} word={word} coordinates={data.coordinates} selected={data.selected} select={select} />
                    ))}
            </Canvas>
        </>
    );
};

export default App
